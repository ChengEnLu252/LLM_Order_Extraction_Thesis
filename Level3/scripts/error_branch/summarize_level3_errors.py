from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

from common_error_utils import ensure_dir, get_level3_root


def load_rows(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def save_counter_csv(counter: Counter, key_name: str, value_name: str, path: Path) -> None:
    ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[key_name, value_name])
        writer.writeheader()
        for k, v in counter.items():
            writer.writerow({key_name: k, value_name: v})


def summarize_one_version(version_name: str, rows: list[dict], out_dir: Path) -> dict:
    field_counter = Counter()
    type_counter = Counter()
    category_counter = Counter()

    for row in rows:
        field_counter[row["error_field"]] += 1
        type_counter[row.get("final_error_type", row.get("suspected_error_type", "other"))] += 1
        category_counter[row["category"]] += 1

    save_counter_csv(field_counter, "error_field", "count", out_dir / f"{version_name}_field_summary.csv")
    save_counter_csv(type_counter, "error_type", "count", out_dir / f"{version_name}_type_summary.csv")
    save_counter_csv(category_counter, "category", "count", out_dir / f"{version_name}_category_summary.csv")

    return {
        "version": version_name,
        "total_field_errors": len(rows),
        "top_error_field": field_counter.most_common(1)[0][0] if field_counter else "",
        "top_error_field_count": field_counter.most_common(1)[0][1] if field_counter else 0,
        "top_error_type": type_counter.most_common(1)[0][0] if type_counter else "",
        "top_error_type_count": type_counter.most_common(1)[0][1] if type_counter else 0,
    }


def main() -> None:
    level3_root = get_level3_root()
    out_dir = level3_root / "reports" / "error_branch_summary"
    ensure_dir(out_dir)

    clean_csv = level3_root / "reports" / "error_analysis_clean_baseline" / "clean_baseline_error_cases_classified.csv"
    v1_csv = level3_root / "reports" / "error_analysis_v1_baseline" / "v1_baseline_error_cases_classified.csv"

    clean_rows = load_rows(clean_csv)
    v1_rows = load_rows(v1_csv)

    summary_rows = [
        summarize_one_version("clean_baseline", clean_rows, out_dir),
        summarize_one_version("v1_baseline", v1_rows, out_dir),
    ]

    summary_csv = out_dir / "level3_error_branch_summary.csv"
    with open(summary_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "version",
                "total_field_errors",
                "top_error_field",
                "top_error_field_count",
                "top_error_type",
                "top_error_type_count",
            ],
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"[OK] summary saved -> {summary_csv}")
    print("\n===== Level 3 Error Summary =====")
    for row in summary_rows:
        print(row)


if __name__ == "__main__":
    main()