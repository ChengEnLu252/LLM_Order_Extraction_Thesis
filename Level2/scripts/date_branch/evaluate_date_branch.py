from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List

from common_date_utils import (
    detect_day_month_swap,
    get_level2_root,
    get_stem_to_file_map,
    load_json,
    safe_get_po_date,
)


def compare_json_equal(pred: dict, gt: dict) -> bool:
    """
    目前先保留簡單整份 JSON 比對。
    注意：
    若你原本主實驗的 evaluate_level2.py 有更完整的比較邏輯，
    後續建議直接移植過來替換這裡。
    """
    return pred == gt


def evaluate_prediction_dir(pred_dir: Path, gt_dir: Path) -> dict:
    gt_map = get_stem_to_file_map(gt_dir, (".json",))
    pred_map = get_stem_to_file_map(pred_dir, (".json",))
    common_stems = sorted(set(gt_map) & set(pred_map))

    total_docs = len(common_stems)
    correct_docs = 0

    total_po_date = 0
    correct_po_date = 0

    detailed_rows: List[dict] = []

    for stem in common_stems:
        gt = load_json(gt_map[stem])
        pred = load_json(pred_map[stem])

        gt_date = safe_get_po_date(gt)
        pred_date = safe_get_po_date(pred)

        doc_correct = compare_json_equal(pred, gt)
        if doc_correct:
            correct_docs += 1

        if gt_date is not None:
            total_po_date += 1
            if gt_date == pred_date:
                correct_po_date += 1

        detailed_rows.append({
            "file_name": stem,
            "pred_po_date": pred_date,
            "gt_po_date": gt_date,
            "po_date_correct": gt_date == pred_date,
            "doc_correct": doc_correct,
            "is_day_month_swap_error": (
                False if gt_date == pred_date else detect_day_month_swap(pred_date or "", gt_date or "")
            ),
        })

    return {
        "total_docs": total_docs,
        "correct_docs": correct_docs,
        "document_accuracy": correct_docs / total_docs if total_docs else 0.0,
        "total_po_date": total_po_date,
        "correct_po_date": correct_po_date,
        "po_date_accuracy": correct_po_date / total_po_date if total_po_date else 0.0,
        "details": detailed_rows,
    }


def compute_improvement_metrics(
    baseline_details: List[dict],
    new_details: List[dict],
) -> dict:
    baseline_map = {r["file_name"]: r for r in baseline_details}
    new_map = {r["file_name"]: r for r in new_details}

    ambiguous_error_total = 0
    ambiguous_error_fixed = 0
    originally_correct_total = 0
    originally_correct_broken = 0

    for stem, base_row in baseline_map.items():
        if stem not in new_map:
            continue

        new_row = new_map[stem]

        # 原本是日月對調錯誤
        if base_row["is_day_month_swap_error"]:
            ambiguous_error_total += 1
            if new_row["po_date_correct"]:
                ambiguous_error_fixed += 1

        # 原本正確，後來被改壞
        if base_row["po_date_correct"]:
            originally_correct_total += 1
            if not new_row["po_date_correct"]:
                originally_correct_broken += 1

    return {
        "ambiguous_error_total": ambiguous_error_total,
        "ambiguous_error_fixed": ambiguous_error_fixed,
        "ambiguous_fix_rate": (
            ambiguous_error_fixed / ambiguous_error_total if ambiguous_error_total else 0.0
        ),
        "originally_correct_total": originally_correct_total,
        "originally_correct_broken": originally_correct_broken,
        "overcorrection_rate": (
            originally_correct_broken / originally_correct_total if originally_correct_total else 0.0
        ),
    }


def save_detail_csv(path: Path, rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "file_name",
                "pred_po_date",
                "gt_po_date",
                "po_date_correct",
                "doc_correct",
                "is_day_month_swap_error",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    level2_root = get_level2_root()
    gt_dir = level2_root / "dataset" / "ground_truth_level2"
    report_dir = level2_root / "reports" / "date_branch_analysis"
    report_dir.mkdir(parents=True, exist_ok=True)

    groups = {
        "baseline": level2_root / "results" / "baseline",
        "date_rule_fix": level2_root / "results" / "date_rule_fix",
        "date_candidate_validation": level2_root / "results" / "date_candidate_validation",
        "date_default_ddmm": level2_root / "results" / "date_default_ddmm",
        "date_default_mmdd": level2_root / "results" / "date_default_mmdd",
    }

    results: Dict[str, dict] = {}
    for group_name, pred_dir in groups.items():
        result = evaluate_prediction_dir(pred_dir, gt_dir)
        results[group_name] = result

        detail_csv = report_dir / f"{group_name}_detail.csv"
        save_detail_csv(detail_csv, result["details"])
        print(f"[OK] detail saved -> {detail_csv}")

    baseline_details = results["baseline"]["details"]

    summary_rows = []
    for group_name, result in results.items():
        row = {
            "group_name": group_name,
            "document_accuracy": result["document_accuracy"],
            "correct_docs": result["correct_docs"],
            "total_docs": result["total_docs"],
            "po_date_accuracy": result["po_date_accuracy"],
            "correct_po_date": result["correct_po_date"],
            "total_po_date": result["total_po_date"],
            "ambiguous_error_total": "",
            "ambiguous_error_fixed": "",
            "ambiguous_fix_rate": "",
            "originally_correct_total": "",
            "originally_correct_broken": "",
            "overcorrection_rate": "",
        }

        if group_name != "baseline":
            improve = compute_improvement_metrics(
                baseline_details=baseline_details,
                new_details=result["details"],
            )
            row.update(improve)

        summary_rows.append(row)

    summary_csv = report_dir / "date_branch_summary.csv"
    with open(summary_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "group_name",
                "document_accuracy",
                "correct_docs",
                "total_docs",
                "po_date_accuracy",
                "correct_po_date",
                "total_po_date",
                "ambiguous_error_total",
                "ambiguous_error_fixed",
                "ambiguous_fix_rate",
                "originally_correct_total",
                "originally_correct_broken",
                "overcorrection_rate",
            ],
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"[OK] summary saved -> {summary_csv}")
    print("\n===== Summary =====")
    for row in summary_rows:
        print(row)


if __name__ == "__main__":
    main()