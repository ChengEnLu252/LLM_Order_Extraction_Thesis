from __future__ import annotations

import csv
from pathlib import Path

from common_date_utils import (
    choose_primary_po_date_candidate,
    ensure_dir,
    get_level2_root,
    get_stem_to_file_map,
    infer_format_hint_from_text,
    load_json,
    parse_date_string,
    read_text,
    save_json,
    safe_get_po_date,
)


def decide_candidate_validation_date(
    raw_text: str,
    raw_date_string: str,
    baseline_po_date: str | None,
) -> tuple[str | None, str, str | None, str | None]:
    """
    A2：候選生成＋驗證組
    回傳：
    - selected_date
    - decision_reason
    - candidate_mmdd
    - candidate_ddmm
    """
    parsed = parse_date_string(raw_date_string)
    if not parsed:
        return baseline_po_date, "keep_baseline_unparseable_raw_date", None, None

    # 非歧義格式 -> 直接正規化
    if parsed["direct_normalized"] is not None:
        return (
            parsed["direct_normalized"],
            "direct_normalized_non_ambiguous",
            parsed["candidate_mmdd"],
            parsed["candidate_ddmm"],
        )

    candidate_mmdd = parsed["candidate_mmdd"]
    candidate_ddmm = parsed["candidate_ddmm"]

    # 若是歧義日期，嘗試驗證
    if parsed["is_ambiguous"]:
        format_hint = infer_format_hint_from_text(raw_text)

        if format_hint == "ddmm" and candidate_ddmm is not None:
            return candidate_ddmm, "selected_candidate_ddmm_by_doc_hint", candidate_mmdd, candidate_ddmm

        if format_hint == "mmdd" and candidate_mmdd is not None:
            return candidate_mmdd, "selected_candidate_mmdd_by_doc_hint", candidate_mmdd, candidate_ddmm

        # 如果 baseline 已經等於某一候選，就保留 baseline
        if baseline_po_date in {candidate_mmdd, candidate_ddmm}:
            return baseline_po_date, "keep_baseline_matches_one_candidate", candidate_mmdd, candidate_ddmm

        # 都無法判斷，保守策略：保留 baseline
        return baseline_po_date, "keep_baseline_ambiguous_no_validation_signal", candidate_mmdd, candidate_ddmm

    return baseline_po_date, "keep_baseline_no_candidate_selected", candidate_mmdd, candidate_ddmm


def main() -> None:
    level2_root = get_level2_root()

    raw_order_dir = level2_root / "dataset" / "order_level2"
    baseline_dir = level2_root / "results" / "baseline"
    output_dir = level2_root / "results" / "date_candidate_validation"
    report_dir = level2_root / "reports" / "date_candidate_validation"

    ensure_dir(output_dir)
    ensure_dir(report_dir)

    raw_map = get_stem_to_file_map(raw_order_dir, (".txt",))
    pred_map = get_stem_to_file_map(baseline_dir, (".json",))

    common_stems = sorted(set(raw_map) & set(pred_map))
    print(f"[INFO] matched files: {len(common_stems)}")

    log_rows = []

    for stem in common_stems:
        raw_text = read_text(raw_map[stem])
        pred = load_json(pred_map[stem])

        baseline_po_date = safe_get_po_date(pred)
        primary_match = choose_primary_po_date_candidate(raw_text)

        updated_pred = pred.copy()

        if primary_match is None:
            selected_date = baseline_po_date
            reason = "keep_baseline_no_raw_date_found"
            raw_date_string = None
            raw_date_line = None
            candidate_mmdd = None
            candidate_ddmm = None
        else:
            raw_date_string = primary_match.raw_date
            raw_date_line = primary_match.line_text
            selected_date, reason, candidate_mmdd, candidate_ddmm = decide_candidate_validation_date(
                raw_text=raw_text,
                raw_date_string=raw_date_string,
                baseline_po_date=baseline_po_date,
            )

        if selected_date is not None:
            updated_pred["po_date"] = selected_date

        save_json(updated_pred, output_dir / f"{stem}.json")

        log_rows.append({
            "file_name": stem,
            "raw_date_string": raw_date_string,
            "raw_date_line": raw_date_line,
            "candidate_mmdd": candidate_mmdd,
            "candidate_ddmm": candidate_ddmm,
            "baseline_po_date": baseline_po_date,
            "selected_po_date": updated_pred.get("po_date"),
            "changed": baseline_po_date != updated_pred.get("po_date"),
            "decision_reason": reason,
        })

    log_csv = report_dir / "date_candidate_validation_log.csv"
    with open(log_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "file_name",
                "raw_date_string",
                "raw_date_line",
                "candidate_mmdd",
                "candidate_ddmm",
                "baseline_po_date",
                "selected_po_date",
                "changed",
                "decision_reason",
            ],
        )
        writer.writeheader()
        writer.writerows(log_rows)

    print(f"[OK] saved predictions -> {output_dir}")
    print(f"[OK] saved log         -> {log_csv}")


if __name__ == "__main__":
    main()