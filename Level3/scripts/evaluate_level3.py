import json
import csv
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# =========================
# 路徑設定
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "dataset"
RESULT_DIR = BASE_DIR / "result"
REPORT_DIR = BASE_DIR / "reports"

# 你現在要評哪一組就改這裡
# clean:
# PRED_DIR = RESULT_DIR / "baseline" / "clean"
# OUTPUT_DIR = REPORT_DIR / "baseline" / "clean"

# v1:
# PRED_DIR = RESULT_DIR / "baseline" / "v1"
# OUTPUT_DIR = REPORT_DIR / "baseline" / "v1"

# v2:
# PRED_DIR = RESULT_DIR / "baseline" / "v2"
# OUTPUT_DIR = REPORT_DIR / "baseline" / "v2"

PRED_DIR = RESULT_DIR / "improved_vision" / "v1"
OUTPUT_DIR = REPORT_DIR / "improved_vision" / "v1"

# ground truth 資料夾
GT_DIR = DATASET_DIR / "ground_truth_level2_source"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =========================
# 評估欄位設定
# =========================
TOP_FIELDS = ["po_number", "po_date", "currency", "total_amount"]
ITEM_FIELDS = ["part_number", "quantity", "unit", "unit_price", "line_amount"]
ALL_FIELDS = TOP_FIELDS + ITEM_FIELDS


# =========================
# 工具函式
# =========================
def infer_category_from_doc_id(doc_id: str) -> str:
    """
    根據檔名推斷 A~E 類別。
    例如:
        L2_A_001 -> A
        L2_B_023 -> B
    """
    parts = doc_id.split("_")
    if len(parts) >= 2:
        return parts[1]
    return "UNKNOWN"


def strip_version_suffix(doc_id: str) -> str:
    """
    將 Level 3 prediction 檔名還原為 ground truth 對應的原始 doc_id。

    例如：
        L2_A_001_v1 -> L2_A_001
        L2_A_001_v2 -> L2_A_001
        L2_A_001    -> L2_A_001
    """
    if doc_id.endswith("_v1"):
        return doc_id[:-3]
    if doc_id.endswith("_v2"):
        return doc_id[:-3]
    return doc_id


def recursive_find_json(base_dir: Path, stem_name: str) -> Optional[Path]:
    """
    在 base_dir 底下遞迴尋找檔名為 {stem_name}.json 的檔案。
    """
    matches = list(base_dir.rglob(f"{stem_name}.json"))
    if not matches:
        return None
    if len(matches) > 1:
        print(f"[WARN] Found multiple ground truth files for {stem_name}, using the first one.")
    return matches[0]


def load_json(json_path: Path) -> Dict[str, Any]:
    """
    讀取 JSON。
    """
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_string(value: Any) -> Any:
    """
    字串標準化：
    - 去除前後空白
    - 空字串視為 None
    """
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return None
        return value

    return value


def normalize_number(value: Any) -> Any:
    """
    數值欄位標準化：
    - None 保持 None
    - 移除逗號
    - 能轉 float 就轉 float
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        value = value.strip().replace(",", "")
        if value == "":
            return None
        try:
            return float(value)
        except Exception:
            return value

    return value


def normalize_quantity(value: Any) -> Any:
    """
    quantity 盡量轉成整數。
    """
    if value is None:
        return None

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return int(value)

    if isinstance(value, str):
        value = value.strip().replace(",", "")
        if value == "":
            return None
        try:
            return int(float(value))
        except Exception:
            return value

    return value


def normalize_top_field(field_name: str, value: Any) -> Any:
    """
    標準化 top-level 欄位。
    """
    if field_name in ["po_number", "po_date", "currency"]:
        return normalize_string(value)
    if field_name == "total_amount":
        return normalize_number(value)
    return value


def normalize_item_field(field_name: str, value: Any) -> Any:
    """
    標準化 item-level 欄位。
    """
    if field_name in ["part_number", "unit"]:
        return normalize_string(value)
    if field_name == "quantity":
        return normalize_quantity(value)
    if field_name in ["unit_price", "line_amount"]:
        return normalize_number(value)
    return value


def safe_get_items(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    安全取得 items；若不存在則回傳空陣列。
    """
    items = data.get("items", [])
    if isinstance(items, list):
        return items
    return []


def compare_top_field(pred: Dict[str, Any], gt: Dict[str, Any], field_name: str) -> Tuple[bool, Any, Any]:
    """
    比較 top-level 欄位。
    回傳:
        (是否相等, pred值, gt值)
    """
    pred_val = normalize_top_field(field_name, pred.get(field_name))
    gt_val = normalize_top_field(field_name, gt.get(field_name))
    return pred_val == gt_val, pred_val, gt_val


def compare_item_field(pred: Dict[str, Any], gt: Dict[str, Any], field_name: str) -> Tuple[bool, Any, Any]:
    """
    比較某個 item-level 欄位。
    規則：
    - items 數量要一致
    - 每一列的該欄位都要一致
    """
    pred_items = safe_get_items(pred)
    gt_items = safe_get_items(gt)

    pred_list = [normalize_item_field(field_name, item.get(field_name)) for item in pred_items]
    gt_list = [normalize_item_field(field_name, item.get(field_name)) for item in gt_items]

    is_equal = pred_list == gt_list
    return is_equal, pred_list, gt_list


def evaluate_single_document(pred_path: Path, gt_path: Path) -> Dict[str, Any]:
    """
    評估單一文件。
    回傳該文件的完整評估結果。
    """
    pred_data = load_json(pred_path)
    gt_data = load_json(gt_path)

    pred_doc_id = pred_path.stem
    gt_doc_id = strip_version_suffix(pred_doc_id)
    category = infer_category_from_doc_id(gt_doc_id)

    field_results = {}
    error_fields = []

    # top-level 欄位
    for field_name in TOP_FIELDS:
        is_equal, pred_val, gt_val = compare_top_field(pred_data, gt_data, field_name)
        field_results[field_name] = {
            "correct": int(is_equal),
            "pred": pred_val,
            "gt": gt_val
        }
        if not is_equal:
            error_fields.append(field_name)

    # item-level 欄位
    for field_name in ITEM_FIELDS:
        is_equal, pred_val, gt_val = compare_item_field(pred_data, gt_data, field_name)
        field_results[field_name] = {
            "correct": int(is_equal),
            "pred": pred_val,
            "gt": gt_val
        }
        if not is_equal:
            error_fields.append(field_name)

    # document correctness：所有欄位全對才算正確
    document_correct = int(all(field_results[f]["correct"] == 1 for f in ALL_FIELDS))

    return {
        "doc_id": pred_doc_id,      # 例如 L2_A_001_v1
        "gt_doc_id": gt_doc_id,     # 例如 L2_A_001
        "category": category,
        "document_correct": document_correct,
        "field_results": field_results,
        "error_fields": error_fields
    }


# =========================
# 報表輸出
# =========================
def write_document_accuracy_csv(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    輸出 document_accuracy.csv
    """
    total_docs = len(results)
    total_correct = sum(r["document_correct"] for r in results)
    overall_acc = total_correct / total_docs if total_docs > 0 else 0.0

    category_groups: Dict[str, List[Dict[str, Any]]] = {}
    for r in results:
        category_groups.setdefault(r["category"], []).append(r)

    rows = [["scope", "total", "correct", "accuracy"]]
    rows.append(["overall", total_docs, total_correct, round(overall_acc, 4)])

    for category in sorted(category_groups.keys()):
        group = category_groups[category]
        total = len(group)
        correct = sum(r["document_correct"] for r in group)
        acc = correct / total if total > 0 else 0.0
        rows.append([category, total, correct, round(acc, 4)])

    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def write_field_accuracy_csv(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    輸出 field_accuracy.csv
    """
    total_docs = len(results)
    rows = [["field_name", "correct", "total", "accuracy"]]

    for field_name in ALL_FIELDS:
        correct_count = sum(r["field_results"][field_name]["correct"] for r in results)
        acc = correct_count / total_docs if total_docs > 0 else 0.0
        rows.append([field_name, correct_count, total_docs, round(acc, 4)])

    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def write_error_report_csv(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    輸出 error_report.csv
    每個錯誤欄位一列。
    """
    rows = [[
        "doc_id",
        "gt_doc_id",
        "category",
        "field_name",
        "pred_value",
        "gt_value"
    ]]

    for r in results:
        for field_name in r["error_fields"]:
            rows.append([
                r["doc_id"],
                r["gt_doc_id"],
                r["category"],
                field_name,
                json.dumps(r["field_results"][field_name]["pred"], ensure_ascii=False),
                json.dumps(r["field_results"][field_name]["gt"], ensure_ascii=False)
            ])

    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


# =========================
# 主流程
# =========================
def main() -> None:
    pred_files = sorted(PRED_DIR.glob("*.json"))

    if not pred_files:
        print(f"[WARN] 在 {PRED_DIR} 找不到任何 prediction json。")
        return

    print(f"[INFO] Prediction directory: {PRED_DIR}")
    print(f"[INFO] Ground truth directory: {GT_DIR}")
    print(f"[INFO] Found {len(pred_files)} prediction files")

    results = []
    missing_gt = []

    for idx, pred_path in enumerate(pred_files, start=1):
        pred_doc_id = pred_path.stem
        gt_doc_id = strip_version_suffix(pred_doc_id)
        gt_path = recursive_find_json(GT_DIR, gt_doc_id)

        if gt_path is None:
            print(f"[WARN] 找不到對應 ground truth: {pred_doc_id} -> {gt_doc_id}")
            missing_gt.append(pred_doc_id)
            continue

        print(f"[INFO] Evaluating {idx}/{len(pred_files)}: {pred_doc_id} (GT: {gt_doc_id})")
        result = evaluate_single_document(pred_path, gt_path)
        results.append(result)

    if not results:
        print("[WARN] 沒有任何成功評估的文件。")
        return

    # 輸出報表
    document_accuracy_path = OUTPUT_DIR / "document_accuracy.csv"
    field_accuracy_path = OUTPUT_DIR / "field_accuracy.csv"
    error_report_path = OUTPUT_DIR / "error_report.csv"

    write_document_accuracy_csv(results, document_accuracy_path)
    write_field_accuracy_csv(results, field_accuracy_path)
    write_error_report_csv(results, error_report_path)

    print("\n[INFO] Evaluation completed.")
    print(f"[INFO] document_accuracy.csv -> {document_accuracy_path}")
    print(f"[INFO] field_accuracy.csv    -> {field_accuracy_path}")
    print(f"[INFO] error_report.csv      -> {error_report_path}")

    if missing_gt:
        print(f"[WARN] 找不到 ground truth 的文件數量：{len(missing_gt)}")
        print(f"[WARN] Missing IDs: {missing_gt[:10]}{' ...' if len(missing_gt) > 10 else ''}")


if __name__ == "__main__":
    main()