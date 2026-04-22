from __future__ import annotations

import csv
from pathlib import Path

from common_error_utils import (
    classify_error_type,
    extract_field_errors,
    get_level3_default_paths,
    get_level3_root,
    get_stem_to_file_map,
    load_json,
    read_text,
    detect_category_from_stem,
    ensure_dir,
)


def export_error_cases(
    version_name: str,
    gt_dir: Path,
    pred_dir: Path,
    ocr_text_dir: Path,
    report_dir: Path,
    result_dir: Path,
) -> None:
    gt_map = get_stem_to_file_map(gt_dir, (".json",))
    pred_map = get_stem_to_file_map(pred_dir, (".json",))
    ocr_map = get_stem_to_file_map(ocr_text_dir, (".txt",))

    common_stems = sorted(set(gt_map) & set(pred_map) & set(ocr_map))
    print(f"[INFO] [{version_name}] matched files: {len(common_stems)}")

    rows = []

    for stem in common_stems:
        gt = load_json(gt_map[stem])
        pred = load_json(pred_map[stem])
        ocr_text = read_text(ocr_map[stem])

        errors = extract_field_errors(gt, pred)

        for err in errors:
            row = {
                "file_name": stem,
                "version": version_name,
                "category": detect_category_from_stem(stem),
                "error_field": err["error_field"],
                "level_type": err["level_type"],
                "item_index": err["item_index"],
                "gt_value": err["gt_value"],
                "pred_value": err["pred_value"],
                "ocr_text_path": str(ocr_map[stem]),
                "prediction_path": str(pred_map[stem]),
                "ground_truth_path": str(gt_map[stem]),
                "suspected_error_type": classify_error_type(
                    error_field=err["error_field"],
                    gt_value=err["gt_value"],
                    pred_value=err["pred_value"],
                    ocr_text=ocr_text,
                ),
                "notes": "",
            }
            rows.append(row)

    ensure_dir(report_dir)
    ensure_dir(result_dir)

    out_csv = report_dir / f"{version_name}_error_cases.csv"
    with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "file_name",
                "version",
                "category",
                "error_field",
                "level_type",
                "item_index",
                "gt_value",
                "pred_value",
                "ocr_text_path",
                "prediction_path",
                "ground_truth_path",
                "suspected_error_type",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] [{version_name}] saved -> {out_csv}")
    print(f"[INFO] [{version_name}] total field errors: {len(rows)}")


def main() -> None:
    level3_root = get_level3_root()
    paths = get_level3_default_paths(level3_root)

    required = {
        "gt_dir": paths["gt_dir"],
        "clean_ocr_text_dir": paths["clean_ocr_text_dir"],
        "v1_ocr_text_dir": paths["v1_ocr_text_dir"],
        "clean_pred_dir": paths["clean_pred_dir"],
        "v1_pred_dir": paths["v1_pred_dir"],
    }

    for name, path in required.items():
        if path is None:
            raise FileNotFoundError(f"Cannot find required directory: {name}")

    export_error_cases(
        version_name="clean_baseline",
        gt_dir=required["gt_dir"],
        pred_dir=required["clean_pred_dir"],
        ocr_text_dir=required["clean_ocr_text_dir"],
        report_dir=level3_root / "reports" / "error_analysis_clean_baseline",
        result_dir=level3_root / "results" / "error_analysis_clean_baseline",
    )

    export_error_cases(
        version_name="v1_baseline",
        gt_dir=required["gt_dir"],
        pred_dir=required["v1_pred_dir"],
        ocr_text_dir=required["v1_ocr_text_dir"],
        report_dir=level3_root / "reports" / "error_analysis_v1_baseline",
        result_dir=level3_root / "results" / "error_analysis_v1_baseline",
    )


if __name__ == "__main__":
    main()