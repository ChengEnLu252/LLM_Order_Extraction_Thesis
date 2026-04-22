from __future__ import annotations

import csv
from pathlib import Path

from common_error_utils import ensure_dir, get_level3_root


def reclassify_csv(input_csv: Path, output_csv: Path) -> None:
    rows = []
    with open(input_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 第一版先保留原本 suspected_error_type
            # 之後如果你想人工調整規則，可在這裡擴充
            row["final_error_type"] = row["suspected_error_type"]
            rows.append(row)

    ensure_dir(output_csv.parent)
    with open(output_csv, "w", encoding="utf-8-sig", newline="") as f:
        fieldnames = list(rows[0].keys()) if rows else []
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] classified -> {output_csv}")


def main() -> None:
    level3_root = get_level3_root()

    clean_in = level3_root / "reports" / "error_analysis_clean_baseline" / "clean_baseline_error_cases.csv"
    clean_out = level3_root / "reports" / "error_analysis_clean_baseline" / "clean_baseline_error_cases_classified.csv"

    v1_in = level3_root / "reports" / "error_analysis_v1_baseline" / "v1_baseline_error_cases.csv"
    v1_out = level3_root / "reports" / "error_analysis_v1_baseline" / "v1_baseline_error_cases_classified.csv"

    reclassify_csv(clean_in, clean_out)
    reclassify_csv(v1_in, v1_out)


if __name__ == "__main__":
    main()