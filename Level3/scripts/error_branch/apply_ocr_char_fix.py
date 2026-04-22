from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from common_error_utils import (
    ensure_dir,
    get_level3_default_paths,
    get_level3_root,
    get_stem_to_file_map,
    load_json,
)

# 上面這行 save_json if False else None 只是避免某些編輯器誤報，
# 如果你看了不爽可以直接刪掉，不影響執行。


def write_json(data: dict, path: Path) -> None:
    """儲存 JSON。"""
    import json
    ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def normalize_upper(text: str) -> str:
    """先做最基本的大寫正規化。"""
    return text.strip().upper()


def fix_po_number(value: Any) -> Tuple[Any, str]:
    """
    修正 po_number。
    預期 pattern 類似：
    PO-2025-7280
    核心規則：
    1. 先轉大寫
    2. 若 prefix 應為 PO，則修正常見混淆
    3. 年份後面的尾碼若應為數字，則把 O/I/L/S/B 修為 0/1/1/5/8
    """
    if value is None:
        return value, "keep_none"

    raw = str(value).strip()
    if raw == "":
        return value, "keep_empty"

    fixed = normalize_upper(raw)
    original_fixed = fixed

    # 嘗試處理像 Po-2024-3362
    fixed = re.sub(r"^P[O0]-", "PO-", fixed)

    # 常見格式：PO-YYYY-NNNN
    m = re.match(r"^(PO)-(\d{4})-([A-Z0-9]+)$", fixed)
    if m:
        prefix, year, tail = m.groups()

        # tail 應該偏數字，因此做保守字元修正
        tail = (
            tail.replace("O", "0")
                .replace("I", "1")
                .replace("L", "1")
                .replace("S", "5")
                .replace("B", "8")
        )

        new_fixed = f"{prefix}-{year}-{tail}"
        if new_fixed != raw:
            return new_fixed, "po_pattern_fix_applied"
        return new_fixed, "po_uppercase_only_or_already_correct"

    # 若不符合主要 pattern，僅做大寫
    if fixed != raw:
        return fixed, "po_uppercase_only"
    return fixed, "po_keep_original"


def fix_part_number(value: Any) -> Tuple[Any, str]:
    """
    修正 part_number。
    根據目前你資料觀察，常見 pattern 類似：
    GX-512
    DX-830
    IR-618
    規則：
    1. 先轉大寫
    2. 若為 字母-數字 型態，對數字尾碼做保守修正
    """
    if value is None:
        return value, "keep_none"

    raw = str(value).strip()
    if raw == "":
        return value, "keep_empty"

    fixed = normalize_upper(raw)

    # 常見 pattern：字母群 + - + 英數尾碼
    m = re.match(r"^([A-Z]+)-([A-Z0-9]+)$", fixed)
    if m:
        head, tail = m.groups()

        # tail 若本來應偏數字，做保守修正
        # 例如 GX-51O -> GX-510
        tail2 = (
            tail.replace("O", "0")
                .replace("I", "1")
                .replace("L", "1")
                .replace("S", "5")
                .replace("B", "8")
        )

        new_fixed = f"{head}-{tail2}"
        if new_fixed != raw:
            return new_fixed, "part_pattern_fix_applied"
        return new_fixed, "part_uppercase_only_or_already_correct"

    if fixed != raw:
        return fixed, "part_uppercase_only"
    return fixed, "part_keep_original"


def apply_fix_to_prediction(pred: dict) -> Tuple[dict, List[dict]]:
    """
    對單份 prediction JSON 套用修正。
    回傳：
    - 修正後 prediction
    - log rows
    """
    updated = pred.copy()
    logs: List[dict] = []

    # 修 header-level: po_number
    old_po = updated.get("po_number")
    new_po, po_reason = fix_po_number(old_po)
    updated["po_number"] = new_po
    logs.append({
        "field_scope": "header",
        "item_index": "",
        "field_name": "po_number",
        "old_value": old_po,
        "new_value": new_po,
        "changed": old_po != new_po,
        "fix_reason": po_reason,
    })

    # 修 item-level: part_number
    items = updated.get("items", [])
    if isinstance(items, list):
        new_items = []
        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                new_items.append(item)
                continue

            new_item = item.copy()
            old_part = new_item.get("part_number")
            new_part, part_reason = fix_part_number(old_part)
            new_item["part_number"] = new_part

            logs.append({
                "field_scope": "item",
                "item_index": idx,
                "field_name": "part_number",
                "old_value": old_part,
                "new_value": new_part,
                "changed": old_part != new_part,
                "fix_reason": part_reason,
            })

            new_items.append(new_item)

        updated["items"] = new_items

    return updated, logs


def process_version(
    version_name: str,
    pred_dir: Path,
    output_dir: Path,
    report_dir: Path,
) -> None:
    pred_map = get_stem_to_file_map(pred_dir, (".json",))
    stems = sorted(pred_map.keys())

    print(f"[INFO] [{version_name}] matched prediction files: {len(stems)}")

    ensure_dir(output_dir)
    ensure_dir(report_dir)

    all_logs = []

    for stem in stems:
        pred = load_json(pred_map[stem])
        updated_pred, logs = apply_fix_to_prediction(pred)

        out_path = output_dir / f"{stem}.json"
        write_json(updated_pred, out_path)

        for row in logs:
            row["file_name"] = stem
            row["version"] = version_name
            all_logs.append(row)

    log_csv = report_dir / f"{version_name}_ocr_char_fix_log.csv"
    with open(log_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "file_name",
                "version",
                "field_scope",
                "item_index",
                "field_name",
                "old_value",
                "new_value",
                "changed",
                "fix_reason",
            ],
        )
        writer.writeheader()
        writer.writerows(all_logs)

    print(f"[OK] [{version_name}] predictions saved -> {output_dir}")
    print(f"[OK] [{version_name}] log saved         -> {log_csv}")


def main() -> None:
    level3_root = get_level3_root()
    paths = get_level3_default_paths(level3_root)

    clean_pred_dir = paths["clean_pred_dir"]
    v1_pred_dir = paths["v1_pred_dir"]

    if clean_pred_dir is None:
        raise FileNotFoundError("clean_pred_dir not found")
    if v1_pred_dir is None:
        raise FileNotFoundError("v1_pred_dir not found")

    process_version(
        version_name="clean_baseline",
        pred_dir=clean_pred_dir,
        output_dir=level3_root / "results" / "ocr_char_fix_clean_baseline",
        report_dir=level3_root / "reports" / "ocr_char_fix_clean_baseline",
    )

    process_version(
        version_name="v1_baseline",
        pred_dir=v1_pred_dir,
        output_dir=level3_root / "results" / "ocr_char_fix_v1_baseline",
        report_dir=level3_root / "reports" / "ocr_char_fix_v1_baseline",
    )


if __name__ == "__main__":
    main()