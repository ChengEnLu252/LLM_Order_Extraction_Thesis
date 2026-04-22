from pathlib import Path

from common_date_utils import ensure_dir, get_level2_root


def main() -> None:
    level2_root = get_level2_root()

    dirs = [
        level2_root / "results" / "date_rule_fix",
        level2_root / "results" / "date_candidate_validation",
        level2_root / "reports" / "date_rule_fix",
        level2_root / "reports" / "date_candidate_validation",
        level2_root / "reports" / "date_branch_analysis",
    ]

    for d in dirs:
        ensure_dir(d)
        print(f"[OK] ensured: {d}")


if __name__ == "__main__":
    main()