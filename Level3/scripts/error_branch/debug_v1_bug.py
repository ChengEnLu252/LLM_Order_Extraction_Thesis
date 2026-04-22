from __future__ import annotations

from pathlib import Path
from typing import Any

from common_error_utils import (
    get_level3_root,
    get_level3_default_paths,
    get_stem_to_file_map,
    load_json,
    read_text,
    extract_field_errors,
)


def preview_mapping(name: str, mapping: dict[str, Path], n: int = 5) -> None:
    keys = sorted(mapping.keys())
    print(f"\n[DEBUG] {name} count = {len(keys)}")
    print(f"[DEBUG] {name} sample stems = {keys[:n]}")
    if keys:
        sample_key = keys[0]
        print(f"[DEBUG] {name} sample path = {mapping[sample_key]}")


def compare_top_level(gt: dict, pred: dict) -> list[tuple[str, Any, Any]]:
    fields = ["po_number", "po_date", "currency", "total_amount"]
    diffs = []
    for f in fields:
        gv = gt.get(f, None)
        pv = pred.get(f, None)
        if gv != pv:
            diffs.append((f, gv, pv))
    return diffs


def main() -> None:
    level3_root = get_level3_root()
    paths = get_level3_default_paths(level3_root)

    print("===== Selected Paths =====")
    for k, v in paths.items():
        print(f"{k}: {v}")

    gt_dir = paths["gt_dir"]
    v1_ocr_text_dir = paths["v1_ocr_text_dir"]
    v1_pred_dir = paths["v1_pred_dir"]

    if gt_dir is None:
        raise FileNotFoundError("gt_dir not found")
    if v1_ocr_text_dir is None:
        raise FileNotFoundError("v1_ocr_text_dir not found")
    if v1_pred_dir is None:
        raise FileNotFoundError("v1_pred_dir not found")

    gt_map = get_stem_to_file_map(gt_dir, (".json",))
    ocr_map = get_stem_to_file_map(v1_ocr_text_dir, (".txt",))
    pred_map = get_stem_to_file_map(v1_pred_dir, (".json",))

    preview_mapping("gt_map", gt_map)
    preview_mapping("ocr_map", ocr_map)
    preview_mapping("pred_map", pred_map)

    gt_keys = set(gt_map.keys())
    ocr_keys = set(ocr_map.keys())
    pred_keys = set(pred_map.keys())

    common_stems = sorted(gt_keys & ocr_keys & pred_keys)

    print("\n===== Stem Matching =====")
    print(f"[DEBUG] gt only sample   = {sorted(gt_keys - pred_keys)[:10]}")
    print(f"[DEBUG] pred only sample = {sorted(pred_keys - gt_keys)[:10]}")
    print(f"[DEBUG] ocr only sample  = {sorted(ocr_keys - gt_keys)[:10]}")
    print(f"[DEBUG] common_stems count = {len(common_stems)}")
    print(f"[DEBUG] common_stems sample = {common_stems[:10]}")

    if not common_stems:
        print("\n[ERROR] No matched stems found for v1.")
        return

    print("\n===== Sample File Comparison =====")
    total_error_rows = 0
    exact_same_json_count = 0

    for stem in common_stems[:10]:
        gt = load_json(gt_map[stem])
        pred = load_json(pred_map[stem])
        ocr_text = read_text(ocr_map[stem])

        field_errors = extract_field_errors(gt, pred)
        top_level_diffs = compare_top_level(gt, pred)

        if gt == pred:
            exact_same_json_count += 1

        total_error_rows += len(field_errors)

        print(f"\n--- {stem} ---")
        print(f"[DEBUG] OCR preview: {ocr_text[:120].replace(chr(10), ' ')}")
        print(f"[DEBUG] top-level diffs count = {len(top_level_diffs)}")
        for item in top_level_diffs[:5]:
            f, gv, pv = item
            print(f"    field={f} | gt={gv} | pred={pv}")

        print(f"[DEBUG] extract_field_errors count = {len(field_errors)}")
        for row in field_errors[:5]:
            print(
                f"    error_field={row['error_field']}, "
                f"level_type={row['level_type']}, "
                f"item_index={row['item_index']}, "
                f"gt={row['gt_value']}, pred={row['pred_value']}"
            )

    print("\n===== Quick Diagnosis =====")
    print(f"[DEBUG] first 10 files exact_same_json_count = {exact_same_json_count}")
    print(f"[DEBUG] first 10 files total_error_rows = {total_error_rows}")

    if total_error_rows == 0:
        print(
            "[DIAGNOSIS] 前 10 份檔案中，extract_field_errors 沒抓到任何差異。\n"
            "可能原因：\n"
            "1. v1 prediction 路徑抓錯了\n"
            "2. prediction 其實不是你要的 baseline 輸出\n"
            "3. ground truth 對到錯資料\n"
            "4. prediction 與 ground truth 內容格式非常接近，需要更細的比較邏輯"
        )
    else:
        print(
            "[DIAGNOSIS] v1 其實有錯誤，表示 bug 大概率出在 build / classify / summarize 某一段流程，而不是資料本身。"
        )


if __name__ == "__main__":
    main()