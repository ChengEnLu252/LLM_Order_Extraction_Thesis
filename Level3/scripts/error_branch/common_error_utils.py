from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def get_level3_root() -> Path:
    """
    假設本檔案位於：
    Level3/scripts/error_branch/common_error_utils.py
    則 Level3 根目錄為 parents[2]
    """
    return Path(__file__).resolve().parents[2]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_text(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def get_stem_to_file_map(folder: Path, suffixes: Tuple[str, ...]) -> Dict[str, Path]:
    """
    遞迴掃描資料夾，建立 stem -> path 的對照表
    若 stem 結尾為 _v1，會自動正規化回原始 stem，
    例如 L2_A_001_v1 -> L2_A_001
    """
    mapping: Dict[str, Path] = {}
    if not folder.exists():
        return mapping

    for file_path in folder.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in suffixes:
            stem = file_path.stem

            # 將 v1 檔名正規化，對齊 ground truth
            if stem.endswith("_v1"):
                stem = stem[:-3]

            if stem in mapping:
                raise ValueError(
                    f"Duplicate stem detected: {stem}\n"
                    f"Existing: {mapping[stem]}\n"
                    f"New: {file_path}"
                )
            mapping[stem] = file_path

    return mapping


def find_first_existing_dir(level3_root: Path, candidates: List[str]) -> Optional[Path]:
    """
    依序嘗試候選路徑，回傳第一個存在的資料夾
    """
    for rel in candidates:
        p = level3_root / rel
        if p.exists() and p.is_dir():
            return p
    return None


def detect_category_from_stem(stem: str) -> str:
    """
    例如：
    L2_A_001 -> A
    L2_B_031 -> B
    """
    m = re.match(r"^L2_([A-E])_\d+$", stem)
    if m:
        return m.group(1)
    return "UNKNOWN"


def safe_get(obj: dict, key: str) -> Any:
    return obj.get(key, None)


def normalize_scalar(value: Any) -> Any:
    """
    做簡單正規化，避免因型別或字串空白造成誤判。
    """
    if value is None:
        return None

    if isinstance(value, str):
        v = value.strip()
        if v == "":
            return None
        return v

    return value


def scalar_equal(a: Any, b: Any) -> bool:
    a = normalize_scalar(a)
    b = normalize_scalar(b)

    # 數字與字串數字容錯
    try:
        if a is not None and b is not None:
            if str(a).replace(",", "") == str(b).replace(",", ""):
                return True
            if float(str(a).replace(",", "")) == float(str(b).replace(",", "")):
                return True
    except Exception:
        pass

    return a == b


def detect_day_month_swap(pred: str, gt: str) -> bool:
    """
    檢查是否屬於 YYYY-MM-DD 的月日對調
    """
    try:
        py, pm, pd = pred.split("-")
        gy, gm, gd = gt.split("-")
    except Exception:
        return False

    return py == gy and pm == gd and pd == gm


def looks_like_ocr_char_confusion(gt_value: Any, pred_value: Any) -> bool:
    """
    粗略判斷是否像 OCR 字元混淆
    適合 po_number / part_number 等英數混合欄位
    """
    if gt_value is None or pred_value is None:
        return False

    gt = str(gt_value).strip()
    pred = str(pred_value).strip()

    if gt == pred:
        return False

    # 長度差太大，通常不只是單純字元混淆
    if abs(len(gt) - len(pred)) > 2:
        return False

    confusion_pairs = [
        ("O", "0"), ("0", "O"),
        ("I", "1"), ("1", "I"),
        ("L", "1"), ("1", "L"),
        ("B", "8"), ("8", "B"),
        ("S", "5"), ("5", "S"),
        ("Z", "2"), ("2", "Z"),
    ]

    gt2 = gt
    for a, b in confusion_pairs:
        gt2 = gt2.replace(a, b)

    pred2 = pred
    for a, b in confusion_pairs:
        pred2 = pred2.replace(a, b)

    # 忽略大小寫與破折號差異做粗略比對
    def simplify(x: str) -> str:
        return x.replace("-", "").replace("_", "").replace(" ", "").upper()

    return simplify(gt2) == simplify(pred2)


def extract_field_errors(gt: dict, pred: dict) -> List[dict]:
    """
    將一份文件的差異展開成「一個錯誤欄位一列」
    """
    rows: List[dict] = []

    top_fields = ["po_number", "po_date", "currency", "total_amount"]
    for field in top_fields:
        gt_val = safe_get(gt, field)
        pred_val = safe_get(pred, field)
        if not scalar_equal(gt_val, pred_val):
            rows.append({
                "error_field": field,
                "level_type": "header",
                "item_index": "",
                "gt_value": gt_val,
                "pred_value": pred_val,
            })

    gt_items = gt.get("items", []) or []
    pred_items = pred.get("items", []) or []
    max_len = max(len(gt_items), len(pred_items))

    item_fields = ["part_number", "quantity", "unit", "unit_price", "line_amount"]

    for idx in range(max_len):
        gt_item = gt_items[idx] if idx < len(gt_items) else {}
        pred_item = pred_items[idx] if idx < len(pred_items) else {}

        for field in item_fields:
            gt_val = gt_item.get(field, None) if isinstance(gt_item, dict) else None
            pred_val = pred_item.get(field, None) if isinstance(pred_item, dict) else None

            if not scalar_equal(gt_val, pred_val):
                rows.append({
                    "error_field": field,
                    "level_type": "item",
                    "item_index": idx,
                    "gt_value": gt_val,
                    "pred_value": pred_val,
                })

    return rows


def classify_error_type(
    error_field: str,
    gt_value: Any,
    pred_value: Any,
    ocr_text: str,
) -> str:
    """
    第一版先做規則式粗分類
    """
    gt_str = "" if gt_value is None else str(gt_value).strip()
    pred_str = "" if pred_value is None else str(pred_value).strip()

    # 1. 日期歧義
    if error_field == "po_date" and gt_str and pred_str:
        if detect_day_month_swap(pred_str, gt_str):
            return "date_ambiguity"

    # 2. OCR 字元混淆
    if error_field in {"po_number", "part_number"}:
        if looks_like_ocr_char_confusion(gt_str, pred_str):
            return "ocr_char_confusion"

    # 3. item-level 可能的數值對應錯位
    if error_field in {"quantity", "unit_price", "line_amount"}:
        if gt_str and pred_str:
            return "value_misalignment"

    # 4. item-level 結構破壞
    if error_field in {"part_number", "quantity", "unit", "unit_price", "line_amount"}:
        text_hint = ocr_text[:1000]
        if "|" in text_hint or ":" in text_hint or "/" in text_hint:
            return "structure_break"

    return "other"


def get_level3_default_paths(level3_root: Path) -> Dict[str, Optional[Path]]:
    """
    自動嘗試找常見路徑
    """

    paths = {
        "gt_dir": find_first_existing_dir(level3_root, [
            "dataset/ground_truth_level2",
            "dataset/ground_truth_level2_source",
            "dataset/ground_truth_level3",
            "dataset/ground_truth",
            "ground_truth_level2",
            "ground_truth_level2_source",
            "ground_truth_level3",
            "ground_truth",
        ]),
        "clean_ocr_text_dir": find_first_existing_dir(level3_root, [
            "dataset/order_level3_ocr_clean_resize_70",
            "dataset/order_level3_ocr_clean_resize",
            "dataset/order_level3_ocr_clean",
            "order_level3_ocr_clean_resize_70",
            "order_level3_ocr_clean_resize",
            "order_level3_ocr_clean",
        ]),
        "v1_ocr_text_dir": find_first_existing_dir(level3_root, [
            "dataset/order_level3_ocr_v1_resize_70",
            "dataset/order_level3_ocr_v1_resize",
            "dataset/order_level3_ocr_v1",
            "order_level3_ocr_v1_resize_70",
            "order_level3_ocr_v1_resize",
            "order_level3_ocr_v1",
        ]),
        "clean_pred_dir": find_first_existing_dir(level3_root, [
            "result/baseline/clean",
            "results/baseline/clean",
            "result/clean_baseline",
            "results/clean_baseline",
            "result/ocr_clean_baseline",
            "results/ocr_clean_baseline",
            "baseline/clean",
            "clean_baseline",
            "ocr_clean_baseline",
        ]),
        "v1_pred_dir": find_first_existing_dir(level3_root, [
            "result/baseline/v1",
            "results/baseline/v1",
            "result/v1_baseline",
            "results/v1_baseline",
            "result/ocr_v1_baseline",
            "results/ocr_v1_baseline",
            "baseline/v1",
            "v1_baseline",
            "ocr_v1_baseline",
        ]),
    }
    return paths

def save_json(data: dict, path: Path) -> None:
    ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def normalize_po_number(value: Any) -> Any:
    """
    專門處理 po_number 的保守修正：
    1. 去空白
    2. 轉大寫
    3. 若符合 PO-YYYY-XXXX 類型，將尾段常見 o/O 修為 0
    """
    if value is None:
        return None

    text = str(value).strip().upper()

    # 常見情況：PO-2025-728O -> PO-2025-7280
    m = re.fullmatch(r"(PO-\d{4}-)([A-Z0-9]+)", text)
    if m:
        prefix = m.group(1)
        suffix = m.group(2)
        suffix = suffix.replace("O", "0").replace("I", "1").replace("L", "1")
        text = prefix + suffix

    return text


def normalize_part_number(value: Any) -> Any:
    """
    專門處理 part_number 的保守修正：
    1. 去空白
    2. 轉大寫
    3. 僅做非常輕量的字元修正，避免過度修正
    """
    if value is None:
        return None

    text = str(value).strip().upper()

    # 僅在全字串已偏向英數料號格式時，做保守修正
    # 例如 GX-512、IR-618、DX-830
    if re.fullmatch(r"[A-Z0-9\-]+", text):
        text = text.replace(" ", "")
        # 這裡先不大幅替換數字/字母，避免誤傷
        # 後續若需要再擴充
    return text