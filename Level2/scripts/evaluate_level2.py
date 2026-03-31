import os
import json
import csv
from pathlib import Path

# ========= 實驗版本設定 =========
# 可改成 "baseline" 或 "improved"
#experiment_name = "baseline"
experiment_name = "improved"

# ========= 路徑設定 =========
base_dir = Path(__file__).resolve().parent

ground_truth_dir = base_dir / "dataset" / "ground_truth_level2"
prediction_dir = base_dir / "results" / experiment_name
report_dir = base_dir / "reports" / experiment_name

report_dir.mkdir(parents=True, exist_ok=True)

# ========= 類別資料夾 =========
category_dirs = {
    "A": "A_field_variation",
    "B": "B_scattered_fields",
    "C": "C_complex_items",
    "D": "D_noise_information",
    "E": "E_mixed_complexity",
}

# ========= 欄位設定 =========
header_fields = ["po_number", "po_date", "currency", "total_amount"]
item_fields = ["part_number", "quantity", "unit", "unit_price", "line_amount"]


def load_json(file_path: Path):
    """
    讀取 JSON 檔案
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def compare_values(gt, pred):
    """
    比較兩個值是否相等

    規則：
    1. None 必須兩邊都相同
    2. 數字允許極小誤差
    3. 字串去除前後空白後比較
    """
    if gt is None or pred is None:
        return gt == pred

    # 若其中一邊是字串數字、另一邊是數值，嘗試轉 float 比較
    try:
        if isinstance(gt, (int, float, str)) and isinstance(pred, (int, float, str)):
            gt_num = float(gt)
            pred_num = float(pred)
            return abs(gt_num - pred_num) < 0.01
    except (ValueError, TypeError):
        pass

    if isinstance(gt, str) and isinstance(pred, str):
        return gt.strip() == pred.strip()

    return gt == pred


def init_field_stats():
    """
    初始化每個欄位的統計器
    """
    stats = {}
    for field in header_fields + item_fields:
        stats[field] = {"correct": 0, "total": 0}
    return stats


def init_category_stats():
    """
    初始化每個 category 的文件統計
    """
    stats = {}
    for code, folder_name in category_dirs.items():
        stats[folder_name] = {
            "category_code": code,
            "correct_docs": 0,
            "total_docs": 0,
        }
    return stats


def evaluate_single_file(file_name, gt_data, pred_data, field_stats, error_rows, category_name):
    """
    評估單一檔案，更新：
    1. field_stats：每個欄位的統計
    2. error_rows：錯誤案例紀錄

    回傳：
    - header_correct
    - header_total
    - item_correct
    - item_total
    - document_all_correct
    """
    header_correct = 0
    header_total = len(header_fields)

    # ===== Header 比較 =====
    for field in header_fields:
        gt_value = gt_data.get(field)
        pred_value = pred_data.get(field)

        field_stats[field]["total"] += 1

        is_correct = compare_values(gt_value, pred_value)
        if is_correct:
            field_stats[field]["correct"] += 1
            header_correct += 1
        else:
            error_rows.append({
                "category": category_name,
                "file_name": file_name,
                "section": "header",
                "item_index": "",
                "field": field,
                "ground_truth": json.dumps(gt_value, ensure_ascii=False),
                "prediction": json.dumps(pred_value, ensure_ascii=False)
            })

    # ===== Item 比較 =====
    gt_items = gt_data.get("items", [])
    pred_items = pred_data.get("items", [])

    item_correct = 0
    item_total = 0

    # item 數量不一致也記錄
    if len(gt_items) != len(pred_items):
        error_rows.append({
            "category": category_name,
            "file_name": file_name,
            "section": "items",
            "item_index": "",
            "field": "item_count",
            "ground_truth": len(gt_items),
            "prediction": len(pred_items)
        })

    min_len = min(len(gt_items), len(pred_items))

    for idx in range(min_len):
        gt_item = gt_items[idx]
        pred_item = pred_items[idx]

        for field in item_fields:
            gt_value = gt_item.get(field)
            pred_value = pred_item.get(field)

            field_stats[field]["total"] += 1
            item_total += 1

            is_correct = compare_values(gt_value, pred_value)
            if is_correct:
                field_stats[field]["correct"] += 1
                item_correct += 1
            else:
                error_rows.append({
                    "category": category_name,
                    "file_name": file_name,
                    "section": "item",
                    "item_index": idx,
                    "field": field,
                    "ground_truth": json.dumps(gt_value, ensure_ascii=False),
                    "prediction": json.dumps(pred_value, ensure_ascii=False)
                })

    # gt_items 比 pred_items 多：漏抽
    for idx in range(min_len, len(gt_items)):
        gt_item = gt_items[idx]
        for field in item_fields:
            gt_value = gt_item.get(field)

            field_stats[field]["total"] += 1
            item_total += 1

            error_rows.append({
                "category": category_name,
                "file_name": file_name,
                "section": "item",
                "item_index": idx,
                "field": field,
                "ground_truth": json.dumps(gt_value, ensure_ascii=False),
                "prediction": "MISSING"
            })

    # pred_items 比 gt_items 多：多抽
    for idx in range(min_len, len(pred_items)):
        pred_item = pred_items[idx]
        for field in item_fields:
            pred_value = pred_item.get(field)

            error_rows.append({
                "category": category_name,
                "file_name": file_name,
                "section": "item",
                "item_index": idx,
                "field": field,
                "ground_truth": "EXTRA",
                "prediction": json.dumps(pred_value, ensure_ascii=False)
            })

    document_all_correct = (
        header_correct == header_total and
        item_correct == item_total and
        len(gt_items) == len(pred_items)
    )

    return header_correct, header_total, item_correct, item_total, document_all_correct


def save_field_accuracy_csv(field_stats, output_path: Path):
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["field", "correct", "total", "accuracy"])

        for field, stats in field_stats.items():
            correct = stats["correct"]
            total = stats["total"]
            accuracy = correct / total if total > 0 else 0
            writer.writerow([field, correct, total, f"{accuracy:.4f}"])


def save_error_report_csv(error_rows, output_path: Path):
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["category", "file_name", "section", "item_index", "field", "ground_truth", "prediction"]
        )
        writer.writeheader()
        writer.writerows(error_rows)


def save_document_accuracy_csv(document_rows, output_path: Path):
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "category",
                "file_name",
                "header_correct",
                "header_total",
                "item_correct",
                "item_total",
                "document_all_correct"
            ]
        )
        writer.writeheader()
        writer.writerows(document_rows)


def save_category_accuracy_csv(category_stats, output_path: Path):
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["category_code", "category_name", "correct_docs", "total_docs", "document_accuracy"])

        for category_name, stats in category_stats.items():
            total_docs = stats["total_docs"]
            correct_docs = stats["correct_docs"]
            acc = correct_docs / total_docs if total_docs > 0 else 0
            writer.writerow([
                stats["category_code"],
                category_name,
                correct_docs,
                total_docs,
                f"{acc:.4f}"
            ])


def print_field_accuracy(field_stats):
    print("\n========== 各欄位 Accuracy ==========")
    for field, stats in field_stats.items():
        correct = stats["correct"]
        total = stats["total"]
        accuracy = correct / total if total > 0 else 0
        print(f"{field:15s}: {accuracy:.4f} ({correct}/{total})")
    print("=====================================")


def main():
    field_stats = init_field_stats()
    category_stats = init_category_stats()
    error_rows = []
    document_rows = []

    total_header_correct = 0
    total_header_count = 0
    total_item_correct = 0
    total_item_count = 0
    total_doc_correct = 0
    total_doc_count = 0

    # ===== 以 prediction 為主進行評估 =====
    # 適合你目前只有抽樣 10 份 prediction 的階段
    for _, category_name in category_dirs.items():
        pred_category_dir = prediction_dir / category_name
        gt_category_dir = ground_truth_dir / category_name

        if not pred_category_dir.exists():
            print(f"[跳過] 找不到 prediction 類別資料夾：{pred_category_dir}")
            continue

        pred_files = sorted([f for f in pred_category_dir.iterdir() if f.suffix == ".json"])

        for pred_file in pred_files:
            file_name = pred_file.name
            gt_path = gt_category_dir / file_name

            if not gt_path.exists():
                print(f"[跳過] 找不到對應 ground truth：{gt_path}")
                continue

            gt_data = load_json(gt_path)
            pred_data = load_json(pred_file)

            if "error" in pred_data:
                print(f"[錯誤] prediction 無法解析 JSON：{category_name}/{file_name}")
                total_doc_count += 1
                category_stats[category_name]["total_docs"] += 1
                error_rows.append({
                    "category": category_name,
                    "file_name": file_name,
                    "section": "file",
                    "item_index": "",
                    "field": "json_parse",
                    "ground_truth": "valid json expected",
                    "prediction": json.dumps(pred_data, ensure_ascii=False)
                })
                continue

            header_correct, header_total, item_correct, item_total, doc_correct = evaluate_single_file(
                file_name=file_name,
                gt_data=gt_data,
                pred_data=pred_data,
                field_stats=field_stats,
                error_rows=error_rows,
                category_name=category_name
            )

            total_header_correct += header_correct
            total_header_count += header_total
            total_item_correct += item_correct
            total_item_count += item_total
            total_doc_correct += int(doc_correct)
            total_doc_count += 1

            category_stats[category_name]["total_docs"] += 1
            category_stats[category_name]["correct_docs"] += int(doc_correct)

            document_rows.append({
                "category": category_name,
                "file_name": file_name,
                "header_correct": header_correct,
                "header_total": header_total,
                "item_correct": item_correct,
                "item_total": item_total,
                "document_all_correct": int(doc_correct)
            })

    # ===== 整體結果 =====
    header_acc = total_header_correct / total_header_count if total_header_count else 0
    item_acc = total_item_correct / total_item_count if total_item_count else 0
    doc_acc = total_doc_correct / total_doc_count if total_doc_count else 0

    print(f"\n========== 整體評估結果（{experiment_name}）==========")
    print(f"Header Accuracy   : {header_acc:.4f} ({total_header_correct}/{total_header_count})")
    print(f"Item Accuracy     : {item_acc:.4f} ({total_item_correct}/{total_item_count})")
    print(f"Document Accuracy : {doc_acc:.4f} ({total_doc_correct}/{total_doc_count})")
    print("==============================================")

    print_field_accuracy(field_stats)

    # ===== 輸出報表 =====
    save_field_accuracy_csv(field_stats, report_dir / "field_accuracy.csv")
    save_error_report_csv(error_rows, report_dir / "error_report.csv")
    save_document_accuracy_csv(document_rows, report_dir / "document_accuracy.csv")
    save_category_accuracy_csv(category_stats, report_dir / "category_accuracy.csv")

    print(f"\n報表已輸出到 reports/{experiment_name}/ 資料夾：")
    print("- field_accuracy.csv")
    print("- error_report.csv")
    print("- document_accuracy.csv")
    print("- category_accuracy.csv")


if __name__ == "__main__":
    main()