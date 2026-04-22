from __future__ import annotations

import csv
from pathlib import Path

from common_date_utils import (
    choose_primary_po_date_candidate,
    detect_day_month_swap,
    get_level2_root,
    get_stem_to_file_map,
    load_json,
    read_text,
    safe_get_po_date,
)


def main() -> None:
    level2_root = get_level2_root()

    raw_order_dir = level2_root / "dataset" / "order_level2"
    gt_dir = level2_root / "dataset" / "ground_truth_level2"
    baseline_dir = level2_root / "results" / "baseline"
    report_dir = level2_root / "reports" / "date_branch_analysis"
    report_dir.mkdir(parents=True, exist_ok=True)

    raw_map = get_stem_to_file_map(raw_order_dir, (".txt",))
    gt_map = get_stem_to_file_map(gt_dir, (".json",))
    pred_map = get_stem_to_file_map(baseline_dir, (".json",))

    common_stems = sorted(set(raw_map) & set(gt_map) & set(pred_map))
    print(f"[INFO] matched files: {len(common_stems)}")

    all_case_csv = report_dir / "all_po_date_cases.csv"
    error_case_csv = report_dir / "po_date_error_cases.csv"

    all_rows = []
    error_rows = []

    for stem in common_stems:
        raw_text = read_text(raw_map[stem])
        gt = load_json(gt_map[stem])
        pred = load_json(pred_map[stem])

        gt_date = safe_get_po_date(gt)
        pred_date = safe_get_po_date(pred)

        primary_match = choose_primary_po_date_candidate(raw_text)
        raw_date_string = primary_match.raw_date if primary_match else None
        raw_date_line = primary_match.line_text if primary_match else None

        is_correct = gt_date == pred_date
        is_day_month_swap = False
        if gt_date and pred_date and not is_correct:
            is_day_month_swap = detect_day_month_swap(pred_date, gt_date)

        row = {
            "file_name": stem,
            "raw_date_string": raw_date_string,
            "raw_date_line": raw_date_line,
            "predicted_po_date": pred_date,
            "ground_truth_po_date": gt_date,
            "is_correct": is_correct,
            "is_day_month_swap": is_day_month_swap,
        }
        all_rows.append(row)

        if not is_correct:
            error_rows.append(row)

    # 輸出全部案例
    with open(all_case_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "file_name",
                "raw_date_string",
                "raw_date_line",
                "predicted_po_date",
                "ground_truth_po_date",
                "is_correct",
                "is_day_month_swap",
            ],
        )
        writer.writeheader()
        writer.writerows(all_rows)

    # 輸出錯誤案例
    with open(error_case_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "file_name",
                "raw_date_string",
                "raw_date_line",
                "predicted_po_date",
                "ground_truth_po_date",
                "is_correct",
                "is_day_month_swap",
            ],
        )
        writer.writeheader()
        writer.writerows(error_rows)

    print(f"[OK] saved all cases    -> {all_case_csv}")
    print(f"[OK] saved error cases  -> {error_case_csv}")
    print(f"[INFO] total errors     -> {len(error_rows)}")
    print(f"[INFO] day-month swaps  -> {sum(1 for r in error_rows if r['is_day_month_swap'])}")


if __name__ == "__main__":
    main()