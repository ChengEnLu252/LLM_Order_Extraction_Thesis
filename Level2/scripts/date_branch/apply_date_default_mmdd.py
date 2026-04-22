from __future__ import annotations

import csv

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


def decide_default_mmdd_date(
    raw_text: str,
    raw_date_string: str,
    baseline_po_date: str | None,
) -> tuple[str | None, str]:
    """
    A3-mmdd：
    對歧義日期，若無額外線索，一律預設為 mm/dd/yyyy。
    """

    parsed = parse_date_string(raw_date_string)
    if not parsed:
        return baseline_po_date, "keep_baseline_unparseable_raw_date"

    # yyyy-mm-dd / yyyy/mm/dd / 非歧義可直接判斷
    if parsed["direct_normalized"] is not None:
        return parsed["direct_normalized"], "direct_normalized_non_ambiguous"

    # 歧義日期：先看文件內有沒有明確 hint
    if parsed["is_ambiguous"]:
        format_hint = infer_format_hint_from_text(raw_text)

        if format_hint == "ddmm" and parsed["candidate_ddmm"] is not None:
            return parsed["candidate_ddmm"], "ambiguous_resolved_by_doc_hint_ddmm"

        if format_hint == "mmdd" and parsed["candidate_mmdd"] is not None:
            return parsed["candidate_mmdd"], "ambiguous_resolved_by_doc_hint_mmdd"

        # 沒有 hint 時，固定採 mm/dd/yyyy
        if parsed["candidate_mmdd"] is not None:
            return parsed["candidate_mmdd"], "ambiguous_default_mmdd"

        return baseline_po_date, "keep_baseline_no_mmdd_candidate"

    return baseline_po_date, "keep_baseline_no_rule_applied"


def main() -> None:
    level2_root = get_level2_root()

    raw_order_dir = level2_root / "dataset" / "order_level2"
    baseline_dir = level2_root / "results" / "baseline"
    output_dir = level2_root / "results" / "date_default_mmdd"
    report_dir = level2_root / "reports" / "date_default_mmdd"

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
        else:
            raw_date_string = primary_match.raw_date
            raw_date_line = primary_match.line_text
            selected_date, reason = decide_default_mmdd_date(
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
            "baseline_po_date": baseline_po_date,
            "selected_po_date": updated_pred.get("po_date"),
            "changed": baseline_po_date != updated_pred.get("po_date"),
            "decision_reason": reason,
        })

    log_csv = report_dir / "date_default_mmdd_log.csv"
    with open(log_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "file_name",
                "raw_date_string",
                "raw_date_line",
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