import os
import json
import time
import base64
from pathlib import Path
from typing import Tuple

from openai import OpenAI


# =========================
# 基本路徑設定
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "dataset"
RESULT_DIR = BASE_DIR / "result"

# 先從 clean 開始；之後要跑 v1 再改
INPUT_DIR = DATASET_DIR / "order_level3_images_v1_resize_70"
OUTPUT_DIR = RESULT_DIR / "improved_vision" / "v1"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =========================
# OpenAI 設定
# =========================
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise ValueError("找不到 OPENAI_API_KEY，請先設定環境變數。")

client = OpenAI(api_key=api_key)

# 這裡請填你在專案中可用、且支援 image input 的模型名稱
MODEL_NAME = "gpt-4o-mini"


# =========================
# Schema 定義
# =========================
schema = {
    "po_number": None,
    "po_date": None,
    "currency": None,
    "total_amount": None,
    "items": [
        {
            "part_number": None,
            "quantity": None,
            "unit": None,
            "unit_price": None,
            "line_amount": None
        }
    ]
}


# =========================
# Prompt 建立
# =========================
# def build_prompt() -> str:
#     """
#     建立 vision direct baseline prompt。
#     這裡沿用你 Level 1 / Level 2 的 baseline 中文規則，
#     但輸入來源改成圖片。
#     """
#     prompt = f"""
# 你是一個高精度的訂單資訊抽取系統。
# 你的任務是直接根據輸入的訂單圖片內容，擷取關鍵資訊，並輸出成符合指定 schema 的 JSON。

# 請嚴格遵守以下規則：

# 【輸出規則】
# 1. 只能輸出一個合法的 JSON 物件。
# 2. 不要輸出說明、註解、前言、結尾、Markdown、```json 或任何額外文字。
# 3. 所有欄位都必須存在於輸出的 JSON 中。
# 4. 若文件中沒有明確出現某欄位，請填 null。
# 5. 不可根據常識、幣別習慣、語境或推測自行補值。
# 6. 請直接根據圖片內容判斷，不要假設圖片之外的資訊。

# 【欄位抽取規則】
# 1. po_number：
#    - 提取訂單編號 / 採購單編號 / PO Number / Purchase Order No. / Order Ref / Order ID。
#    - 只能根據圖片中明確標示的編號填寫。

# 2. po_date：
#    - 提取訂單日期 / PO Date / Order Date / Date Issued / Issued On。
#    - 請統一轉換成 YYYY-MM-DD 格式。
#    - 若文件中沒有明確日期，填 null。
#    - 不可把 delivery date、ship date、invoice date 當成 po_date。
#    - 若日期格式為純數字斜線格式（如 05/11/2024），請根據文件慣用格式判讀。
#    - 若無法明確判斷，優先保持與文件整體日期表示邏輯一致，不可任意交換月與日。

# 3. currency：
#    - 只根據圖片中明確出現的幣別資訊填寫。
#    - 若圖片寫的是 USD、US$、U.S. Dollar，統一輸出 "USD"。
#    - 若圖片寫的是 TWD、NTD、NT$，統一輸出 "TWD"。
#    - 若圖片寫的是 EUR、€, Euro，統一輸出 "EUR"。
#    - 若圖片寫的是 JPY、¥、Yen，統一輸出 "JPY"。
#    - 若圖片沒有明確寫出幣別，填 null。
#    - 不可根據供應商地區、語言、金額格式或其他線索猜測幣別。

# 4. total_amount：
#    - 提取整份訂單的最終總金額。
#    - 只保留數字，輸出為數值型態。
#    - 不可把 unit price、line amount 當成 total_amount。
#    - 若圖片同時有 subtotal、tax、shipping fee、discount、handling fee、final payable amount、final amount：
#      請優先選擇圖片中明確代表最終應付總額的欄位。
#    - 若文件沒有明確總金額，填 null。

# 5. items：
#    - 從訂單中的每一筆明細逐列抽取。
#    - 每一筆 item 都必須對應到圖片中的同一列或同一筆明細，不可跨列拼接。
#    - 不可自行合併不同列資訊。
#    - 若沒有任何明細，輸出空陣列 []。

# 6. item 欄位規則：
#    - part_number：提取料號 / 產品編號 / Product Code / SKU / Part No.
#    - quantity：提取數量，輸出整數
#    - unit：提取單位，例如 pcs、EA、boxes、sets、units；若無明確單位則填 null
#    - unit_price：提取單價，僅保留數字
#    - line_amount：提取該列總金額，僅保留數字

# 【標準化規則】
# 1. 日期格式統一為 YYYY-MM-DD。
# 2. 金額與價格只保留數字，不要貨幣符號，不要千分位逗號。
# 3. quantity 請輸出整數。
# 4. 若欄位值無法由圖片內容明確判定，請填 null，不可猜測。

# 【Schema】
# {json.dumps(schema, ensure_ascii=False, indent=2)}
# """
#     return prompt.strip()

def build_prompt() -> str:
    """
    建立 Level 3 improved extraction prompt。
    針對 OCR 文字特性進一步提高約束，降低欄位誤配、
    日期誤判與 item 跨列拼接問題。
    """
    prompt = f"""
你是一個高精度且保守的訂單資訊抽取系統。
你的任務是從 OCR 後的訂單文字中擷取關鍵資訊，並輸出成符合指定 schema 的 JSON。

請注意：輸入文字可能來自 OCR，因此可能存在空格遺失、大小寫混淆、標籤與內容黏連、數字或字母局部辨識錯誤等現象。你必須盡可能根據文件內容進行穩健擷取，但不可自行腦補或猜測不存在的資訊。

請嚴格遵守以下規則：

【輸出規則】
1. 只能輸出一個合法的 JSON 物件。
2. 不要輸出說明、註解、前言、結尾、Markdown、```json 或任何額外文字。
3. 所有欄位都必須存在於輸出的 JSON 中。
4. 若文件中沒有明確出現某欄位，請填 null。
5. 不可根據常識、幣別習慣、地區、語境或推測自行補值。
6. 若 OCR 文字有局部黏連、空格缺失或大小寫不一致，應先依上下文辨識其原意，但不可超出文件可支持的範圍。

【整體判讀原則】
1. 先辨識文件中的表頭區、金額摘要區與明細區，再進行欄位抽取。
2. 若標籤與內容黏在一起（例如 PONumber、DateIssued、BillingCurrency、TotalAmount），應視為標籤與值的連續表達，不可因此忽略該欄位。
3. 若同一欄位候選值有多個，應優先選擇：
   - 與欄位標籤距離最近者
   - 語意最直接對應者
   - 在文件中角色最明確者
4. 對於識別碼、日期、金額與 item 明細，必須優先依據文件中的文字與結構判讀，不可任意修正。
5. 若資訊不足或存在多種可能且無法明確判斷，請填 null，不可猜測。

【欄位抽取規則】
1. po_number：
   - 提取訂單編號 / 採購單編號 / PO Number / Purchase Order No. / Order Ref / Order ID。
   - 只能根據文件中明確標示的編號填寫。
   - 若 OCR 將大小寫混淆（例如 PO / Po）但整體字串仍可對應同一識別碼，請保留文件中辨識出的字串內容，不可自行修正為其他格式。
   - 若 OCR 將字母 O 與數字 0 混淆，但文件無法提供更明確依據時，不可自行猜測替換。

2. po_date：
   - 提取訂單日期 / PO Date / Order Date / Date Issued / Issued On。
   - 請統一轉換成 YYYY-MM-DD 格式。
   - 若文件中沒有明確日期，填 null。
   - 不可把 delivery date、ship date、invoice date 當成 po_date。
   - 若日期格式為純數字斜線格式（如 05/11/2024），請根據文件慣用格式判讀。
   - 若無法明確判斷，優先保持與文件整體日期表示邏輯一致，不可任意交換月與日。
   - 若 OCR 造成日期中局部字元模糊，但仍可由鄰近標籤與整體格式合理判讀，請選擇最保守且最一致的表示；若仍無法確定，填 null。

3. currency：
   - 只根據文件中明確出現的幣別資訊填寫。
   - 若文件寫的是 USD、US$、U.S. Dollar，統一輸出 "USD"。
   - 若文件寫的是 TWD、NTD、NT$，統一輸出 "TWD"。
   - 若文件寫的是 EUR、€, Euro，統一輸出 "EUR"。
   - 若文件寫的是 JPY、¥、Yen，統一輸出 "JPY"。
   - 若文件沒有明確寫出幣別，填 null。
   - 不可根據供應商地區、語言、金額格式或其他線索猜測幣別。
   - 若幣別與欄位標籤黏連，應視為可辨識之明確幣別資訊。

4. total_amount：
   - 提取整份訂單的最終總金額。
   - 只保留數字，輸出為數值型態。
   - 不可把 unit price、line amount 當成 total_amount。
   - 若文件同時有 subtotal、tax、shipping fee、discount、handling fee、final payable amount、final amount：
     請優先選擇文件中明確代表最終應付總額的欄位。
   - 若文件沒有明確總金額，填 null。
   - 若同一頁中存在多個金額，應優先選擇與 Total / Total Amount / Final Amount / Amount Due 等語意最直接對應者。

5. items：
   - 從訂單中的每一筆明細逐列抽取。
   - 每一筆 item 都必須對應到文件中的同一列或同一筆明細，不可跨列拼接。
   - 不可自行合併不同列資訊。
   - 若沒有任何明細，輸出空陣列 []。
   - 若 OCR 造成部分欄位換行，只有在可明確判斷仍屬同一筆明細時，才能視為同一 item；若無法明確判斷，應保守處理，不可任意拼接。

6. item 欄位規則：
   - part_number：提取料號 / 產品編號 / Product Code / SKU / Part No.
   - quantity：提取數量，輸出整數
   - unit：提取單位，例如 pcs、EA、boxes、sets、units；若無明確單位則填 null
   - unit_price：提取單價，僅保留數字
   - line_amount：提取該列總金額，僅保留數字

【明細判讀補充規則】
1. 明細通常依序包含 part_number、quantity、unit、unit_price、line_amount，但實際排列可能因 OCR 而換行。
2. 若文件中每筆明細呈現固定重複模式，應依該模式逐筆抽取。
3. 不可把表頭（如 Quantity、Unit、Unit Price、Line Total）誤當成 item 值。
4. 不可把 remarks、notes、terms、shipping instructions 當成 item。
5. 若某筆 item 缺少部分欄位，僅該欄位填 null，不可整筆捨棄；但若整列無法辨識為有效明細，則不要強行生成該 item。

【標準化規則】
1. 日期格式統一為 YYYY-MM-DD。
2. 金額與價格只保留數字，不要貨幣符號，不要千分位逗號。
3. quantity 請輸出整數。
4. 若欄位值無法由文件內容明確判定，請填 null，不可猜測。

【Schema】
{json.dumps(schema, ensure_ascii=False, indent=2)}
"""
    return prompt.strip()


# =========================
# 圖片編碼
# =========================
def image_to_data_url(image_path: Path) -> str:
    """
    把本地圖片轉成 base64 data URL。
    OpenAI API 支援在 image_url.url 中放入 base64 data URL。
    """
    suffix = image_path.suffix.lower()
    if suffix == ".png":
        mime_type = "image/png"
    elif suffix in [".jpg", ".jpeg"]:
        mime_type = "image/jpeg"
    elif suffix == ".webp":
        mime_type = "image/webp"
    else:
        raise ValueError(f"不支援的圖片格式：{suffix}")

    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    return f"data:{mime_type};base64,{b64}"


# =========================
# 模型呼叫
# =========================
def call_vision_llm(image_path: Path, max_retries: int = 6, sleep_seconds: int = 20) -> str:
    """
    直接把圖片送給多模態模型，要求輸出 JSON。
    """
    prompt = build_prompt()
    image_data_url = image_to_data_url(image_path)

    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_data_url,
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ]
            )
            return response.choices[0].message.content

        except Exception as e:
            last_error = e
            print(f"[WARN] API 呼叫失敗，第 {attempt}/{max_retries} 次重試：{e}")
            time.sleep(sleep_seconds)

    raise RuntimeError(f"API 呼叫失敗，已重試 {max_retries} 次。最後錯誤：{last_error}")


# =========================
# JSON 處理
# =========================
def parse_json_safely(raw_output: str) -> dict:
    """
    安全解析模型輸出。
    """
    try:
        return json.loads(raw_output)
    except Exception as e:
        return {
            "_parse_error": str(e),
            "_raw_output": raw_output
        }


def save_json(output_path: Path, data: dict) -> None:
    """
    儲存 JSON。
    """
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# =========================
# 單筆處理
# =========================
def process_single_image(image_path: Path) -> Tuple[bool, str]:
    """
    單張圖片：
    - 呼叫多模態模型
    - 解析 JSON
    - 存檔
    """
    try:
        raw_output = call_vision_llm(image_path)
        parsed_output = parse_json_safely(raw_output)

        output_path = OUTPUT_DIR / f"{image_path.stem}.json"
        save_json(output_path, parsed_output)

        return True, f"[OK] 已輸出：{output_path.name}"

    except Exception as e:
        return False, f"[ERROR] 處理失敗 {image_path.name}：{e}"


# =========================
# 主流程
# =========================
def main() -> None:
    """
    批次跑 vision direct baseline extraction。
    """
    image_files = []
    for pattern in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
        image_files.extend(INPUT_DIR.glob(pattern))
    image_files = sorted(image_files)

    if not image_files:
        print(f"[WARN] 在 {INPUT_DIR} 找不到任何圖片檔。")
        return

    print(f"[INFO] 讀取資料夾：{INPUT_DIR}")
    print(f"[INFO] 輸出資料夾：{OUTPUT_DIR}")
    print(f"[INFO] 共找到 {len(image_files)} 張圖片")

    success_count = 0
    fail_count = 0

    for idx, image_file in enumerate(image_files, start=1):
        print(f"[INFO] 處理中 {idx}/{len(image_files)}：{image_file.name}")

        ok, message = process_single_image(image_file)
        print(message)
        time.sleep(8)

        if ok:
            success_count += 1
        else:
            fail_count += 1

    print("\n[INFO] Vision baseline extraction 完成")
    print(f"[INFO] 成功：{success_count}")
    print(f"[INFO] 失敗：{fail_count}")


if __name__ == "__main__":
    main()