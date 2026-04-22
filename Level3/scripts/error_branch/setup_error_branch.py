from common_error_utils import ensure_dir, get_level3_root


def main() -> None:
    level3_root = get_level3_root()

    dirs = [
        level3_root / "scripts" / "error_branch",
        level3_root / "results" / "error_analysis_clean_baseline",
        level3_root / "results" / "error_analysis_v1_baseline",
        level3_root / "reports" / "error_analysis_clean_baseline",
        level3_root / "reports" / "error_analysis_v1_baseline",
        level3_root / "reports" / "error_branch_summary",
        level3_root / "results" / "ocr_char_fix_clean_baseline",
        level3_root / "results" / "ocr_char_fix_v1_baseline",
        level3_root / "results" / "field_pattern_fix_clean_baseline",
        level3_root / "results" / "field_pattern_fix_v1_baseline",
        level3_root / "reports" / "ocr_char_fix_clean_baseline",
        level3_root / "reports" / "ocr_char_fix_v1_baseline",
        level3_root / "reports" / "field_pattern_fix_clean_baseline",
        level3_root / "reports" / "field_pattern_fix_v1_baseline",
    ]

    for d in dirs:
        ensure_dir(d)
        print(f"[OK] ensured: {d}")


if __name__ == "__main__":
    main()