from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List, Tuple

from common_error_utils import (
    get_level3_default_paths,
    get_level3_root,
    get_stem_to_file_map,
    load_json,
    scalar_equal,
)


def compare_document(pred: dict, gt: dict) -> bool:
    """
    比較整份文件是否正確。
    採和主實驗更接近的比法：
    - top-level 四欄都要相同
    - items 長度相同
    - 每個 item 的五欄都要相同
    """
    top_fields = ["po_number", "po_date", "currency", "total_amount"]
    for field in top_fields:
        if not scalar_equal(pred.get(field), gt.get(field)):
            return False

    gt_items = gt.get("items", []) or []
    pred_items = pred.get("items", []) or []

    if len(gt_items) != len(pred_items):
        return False

    item_fields = ["part_number", "quantity", "unit", "unit_price", "line_amount"]
    for gt_item, pred_item in zip(gt_items, pred_items):
        for field in item_fields:
            if not scalar_equal(pred_item.get(field), gt_item.get(field)):
                return False

    return True


def get_part_number_pair_counts(gt: dict, pred: dict) -> Tuple[int, int]:
    """
    回傳：
    - total part_number count
    - correct part_number count
    """
    gt_items = gt.get("items", []) or []
    pred_items = pred.get("items", []) or []

    total = len(gt_items)
    correct = 0

    for idx in range(min(len(gt_items), len(pred_items))):
        gt_val = gt_items[idx].get("part_number")
        pred_val = pred_items[idx].get("part_number")
        if scalar_equal(gt_val, pred_val):
            correct += 1

    return total, correct


def evaluate_one_pair(
    baseline_dir: Path,
    fixed_dir: Path,
    gt_dir: Path,
    version_name: str,
    out_dir: Path,
) -> dict:
    gt_map = get_stem_to_file_map(gt_dir, (".json",))
    base_map = get_stem_to_file_map(baseline_dir, (".json",))
    fix_map = get_stem_to_file_map(fixed_dir, (".json",))

    common_stems = sorted(set(gt_map) & set(base_map) & set(fix_map))
    print(f"[INFO] [{version_name}] matched files: {len(common_stems)}")

    base_doc_correct = 0
    fix_doc_correct = 0

    total_po = 0
    base_po_correct = 0
    fix_po_correct = 0

    total_part = 0
    base_part_correct = 0
    fix_part_correct = 0

    po_fix_success = 0
    po_overcorrection = 0
    part_fix_success = 0
    part_overcorrection = 0

    detail_rows = []

    for stem in common_stems:
        gt = load_json(gt_map[stem])
        base = load_json(base_map[stem])
        fix = load_json(fix_map[stem])

        # document accuracy
        base_doc_ok = compare_document(base, gt)
        fix_doc_ok = compare_document(fix, gt)
        if base_doc_ok:
            base_doc_correct += 1
        if fix_doc_ok:
            fix_doc_correct += 1

        # po_number
        gt_po = gt.get("po_number")
        base_po = base.get("po_number")
        fix_po = fix.get("po_number")

        total_po += 1
        base_po_ok = scalar_equal(base_po, gt_po)
        fix_po_ok = scalar_equal(fix_po, gt_po)

        if base_po_ok:
            base_po_correct += 1
        if fix_po_ok:
            fix_po_correct += 1

        if (not base_po_ok) and fix_po_ok:
            po_fix_success += 1
        if base_po_ok and (not fix_po_ok):
            po_overcorrection += 1

        # part_number
        gt_total_part, gt_base_part_correct = get_part_number_pair_counts(gt, base)
        _, gt_fix_part_correct = get_part_number_pair_counts(gt, fix)

        total_part += gt_total_part
        base_part_correct += gt_base_part_correct
        fix_part_correct += gt_fix_part_correct

        # item-level part_number 修正成功 / 誤修正
        gt_items = gt.get("items", []) or []
        base_items = base.get("items", []) or []
        fix_items = fix.get("items", []) or []
        min_len = min(len(gt_items), len(base_items), len(fix_items))

        for idx in range(min_len):
            gt_part = gt_items[idx].get("part_number")
            base_part = base_items[idx].get("part_number")
            fix_part = fix_items[idx].get("part_number")

            base_ok = scalar_equal(base_part, gt_part)
            fix_ok = scalar_equal(fix_part, gt_part)

            if (not base_ok) and fix_ok:
                part_fix_success += 1
            if base_ok and (not fix_ok):
                part_overcorrection += 1

        detail_rows.append({
            "file_name": stem,
            "baseline_doc_correct": base_doc_ok,
            "fixed_doc_correct": fix_doc_ok,
            "baseline_po_number": base_po,
            "fixed_po_number": fix_po,
            "gt_po_number": gt_po,
            "baseline_po_correct": base_po_ok,
            "fixed_po_correct": fix_po_ok,
        })

    ensure_dir = out_dir.mkdir
    out_dir.mkdir(parents=True, exist_ok=True)

    detail_csv = out_dir / f"{version_name}_ocr_char_fix_detail.csv"
    with open(detail_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "file_name",
                "baseline_doc_correct",
                "fixed_doc_correct",
                "baseline_po_number",
                "fixed_po_number",
                "gt_po_number",
                "baseline_po_correct",
                "fixed_po_correct",
            ],
        )
        writer.writeheader()
        writer.writerows(detail_rows)

    summary = {
        "version": version_name,
        "total_docs": len(common_stems),
        "baseline_document_accuracy": base_doc_correct / len(common_stems) if common_stems else 0.0,
        "fixed_document_accuracy": fix_doc_correct / len(common_stems) if common_stems else 0.0,
        "total_po_number": total_po,
        "baseline_po_number_accuracy": base_po_correct / total_po if total_po else 0.0,
        "fixed_po_number_accuracy": fix_po_correct / total_po if total_po else 0.0,
        "po_number_fix_success": po_fix_success,
        "po_number_overcorrection": po_overcorrection,
        "total_part_number": total_part,
        "baseline_part_number_accuracy": base_part_correct / total_part if total_part else 0.0,
        "fixed_part_number_accuracy": fix_part_correct / total_part if total_part else 0.0,
        "part_number_fix_success": part_fix_success,
        "part_number_overcorrection": part_overcorrection,
    }

    return summary


def main() -> None:
    level3_root = get_level3_root()
    paths = get_level3_default_paths(level3_root)

    gt_dir = paths["gt_dir"]
    clean_pred_dir = paths["clean_pred_dir"]
    v1_pred_dir = paths["v1_pred_dir"]

    if gt_dir is None:
        raise FileNotFoundError("gt_dir not found")
    if clean_pred_dir is None:
        raise FileNotFoundError("clean_pred_dir not found")
    if v1_pred_dir is None:
        raise FileNotFoundError("v1_pred_dir not found")

    clean_fixed_dir = level3_root / "results" / "ocr_char_fix_clean_baseline"
    v1_fixed_dir = level3_root / "results" / "ocr_char_fix_v1_baseline"

    report_clean_dir = level3_root / "reports" / "ocr_char_fix_clean_baseline"
    report_v1_dir = level3_root / "reports" / "ocr_char_fix_v1_baseline"
    summary_dir = level3_root / "reports" / "error_branch_summary"
    summary_dir.mkdir(parents=True, exist_ok=True)

    clean_summary = evaluate_one_pair(
        baseline_dir=clean_pred_dir,
        fixed_dir=clean_fixed_dir,
        gt_dir=gt_dir,
        version_name="clean_baseline",
        out_dir=report_clean_dir,
    )

    v1_summary = evaluate_one_pair(
        baseline_dir=v1_pred_dir,
        fixed_dir=v1_fixed_dir,
        gt_dir=gt_dir,
        version_name="v1_baseline",
        out_dir=report_v1_dir,
    )

    summary_rows = [clean_summary, v1_summary]

    summary_csv = summary_dir / "ocr_char_fix_summary.csv"
    with open(summary_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "version",
                "total_docs",
                "baseline_document_accuracy",
                "fixed_document_accuracy",
                "total_po_number",
                "baseline_po_number_accuracy",
                "fixed_po_number_accuracy",
                "po_number_fix_success",
                "po_number_overcorrection",
                "total_part_number",
                "baseline_part_number_accuracy",
                "fixed_part_number_accuracy",
                "part_number_fix_success",
                "part_number_overcorrection",
            ],
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"[OK] summary saved -> {summary_csv}")
    print("\n===== OCR Char Fix Summary =====")
    for row in summary_rows:
        print(row)


if __name__ == "__main__":
    main()