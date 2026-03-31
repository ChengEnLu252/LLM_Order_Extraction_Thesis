import os
import json
import random
from pathlib import Path
from openai import OpenAI

# 初始化 OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# =========================================================
# 1. 路徑設定
# =========================================================
base_dir = Path(__file__).resolve().parent

# Level 2 訂單資料夾（A~E 子資料夾都在這裡）
orders_dir = base_dir / "dataset" / "order_level2"

# Level 2 抽取結果輸出資料夾
# 建議先放 baseline，之後若有 improved prompt 可再分資料夾
#results_dir = base_dir / "results" / "baseline"
results_dir = base_dir / "results" / "improved"

# 類別資料夾名稱
category_dirs = {
    "A": "A_field_variation",
    "B": "B_scattered_fields",
    "C": "C_complex_items",
    "D": "D_noise_information",
    "E": "E_mixed_complexity",
}

# 建立輸出資料夾
for folder_name in category_dirs.values():
    (results_dir / folder_name).mkdir(parents=True, exist_ok=True)

# 固定隨機種子，讓抽樣可重現
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# =========================================================
# 2. Schema 定義
# =========================================================
schema = {
    "po_number": "string",
    "po_date": "YYYY-MM-DD",
    "currency": "string",
    "total_amount": "float",
    "items": [
        {
            "part_number": "string",
            "quantity": "int",
            "unit": "string",
            "unit_price": "float",
            "line_amount": "float"
        }
    ]
}

# =========================================================
# 3. Prompt
# =========================================================
# def build_prompt(order_text: str) -> str:
#     """
#     建立 Level 2 抽取 Prompt。
#     先沿用你目前較完整的高約束版本，作為 baseline 測試。
#     """

#     prompt = f"""
# 你是一個高精度的訂單資訊抽取系統。
# 你的任務是從訂單文字中擷取關鍵資訊，並輸出成符合指定 schema 的 JSON。

# 請嚴格遵守以下規則：

# 【輸出規則】
# 1. 只能輸出一個合法的 JSON 物件。
# 2. 不要輸出說明、註解、前言、結尾、Markdown、```json 或任何額外文字。
# 3. 所有欄位都必須存在於輸出的 JSON 中。
# 4. 若文件中沒有明確出現某欄位，請填 null。
# 5. 不可根據常識、幣別習慣、語境或推測自行補值。

# 【欄位抽取規則】
# 1. po_number：
#    - 提取訂單編號 / 採購單編號 / PO Number / Purchase Order No. / Order Ref / Order ID。
#    - 只能根據文件中明確標示的編號填寫。

# 2. po_date：
#    - 提取訂單日期 / PO Date / Order Date / Date Issued / Issued On。
#    - 請統一轉換成 YYYY-MM-DD 格式。
#    - 若文件中沒有明確日期，填 null。
#    - 不可把 delivery date、ship date、invoice date 當成 po_date。
#    -若日期格式為純數字斜線格式（如 05/11/2024），請根據文件慣用格式判讀；
#    -若無法明確判斷，優先保持與文件整體日期表示邏輯一致，不可任意交換月與日。

# 3. currency：
#    - 只根據文件中明確出現的幣別資訊填寫。
#    - 若文件寫的是 USD、US$、U.S. Dollar，統一輸出 "USD"。
#    - 若文件寫的是 TWD、NTD、NT$，統一輸出 "TWD"。
#    - 若文件寫的是 EUR、€, Euro，統一輸出 "EUR"。
#    - 若文件寫的是 JPY、¥、Yen，統一輸出 "JPY"。
#    - 若文件沒有明確寫出幣別，填 null。
#    - 不可根據供應商地區、語言、金額格式或其他線索猜測幣別。

# 4. total_amount：
#    - 提取整份訂單的最終總金額。
#    - 只保留數字，輸出為數值型態。
#    - 不可把 unit price、line amount 當成 total_amount。
#    - 若文件同時有 subtotal、tax、shipping fee、discount、handling fee、final payable amount、final amount：
#      請優先選擇文件中明確代表最終應付總額的欄位。
#    - 若文件沒有明確總金額，填 null。

# 5. items：
#    - 從訂單中的每一筆明細逐列抽取。
#    - 每一筆 item 都必須對應到文件中的同一列或同一筆明細，不可跨列拼接。
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
# 4. 若欄位值無法由文件內容明確判定，請填 null，不可猜測。

# 【Schema】
# {json.dumps(schema, ensure_ascii=False, indent=2)}

# 【訂單內容】
# {order_text}
# """
#     return prompt

#improved prompt
def build_prompt(order_text: str) -> str:
    """
    Level 2 Improved Prompt
    設計目標：
    1. 強化複雜文字訂單中的欄位定位能力
    2. 加強日期歧義格式判讀
    3. 加強最終總金額與干擾金額的區分
    4. 提升複雜 item 格式下的逐筆對齊能力
    5. 強化中英文混合欄位名稱的辨識
    """

    prompt = f"""
你是一個高精度的訂單資訊抽取與標準化系統。
你的任務是從訂單文字中擷取關鍵資訊，並輸出成符合指定 schema 的 JSON。

請先完整閱讀整份文件，再進行抽取，不可只根據局部段落、單一關鍵字或單一表面格式做判斷。

====================
【輸出規則】
====================
1. 只能輸出一個合法的 JSON 物件。
2. 不要輸出任何說明、註解、前言、結尾、Markdown、```json 或其他額外文字。
3. 所有 schema 欄位都必須出現在輸出的 JSON 中。
4. 若文件中沒有明確資訊，請填 null。
5. 不可根據常識、慣例、公司所在地、語言或金額樣式自行猜測欄位值。
6. 若文件中有多個相似資訊，請選擇最符合欄位定義的內容，不可任意挑選。

====================
【整體抽取原則】
====================
1. 先辨識 header-level 資訊：
   - po_number
   - po_date
   - currency
   - total_amount

2. 再辨識 item-level 資訊：
   - part_number
   - quantity
   - unit
   - unit_price
   - line_amount

3. 文件中若同時出現：
   - 欄位名稱變異
   - 欄位資訊分散
   - 明細格式不規則
   - subtotal / tax / shipping / discount / handling fee 等干擾資訊
   請仍依欄位語意定義做抽取，不可因欄位位置或名稱不同而忽略正確答案。

====================
【欄位抽取規則】
====================

1. po_number：
- 提取訂單編號 / 採購單編號 / PO Number / Purchase Order No. / P.O. No. / Order Ref / Order ID。
- 只根據文件中明確標示的訂單編號填寫。
- 不可把 invoice number、shipment number、reference code、contact code 當成 po_number。

2. po_date：
- 提取訂單日期 / PO Date / Order Date / Date Issued / Issued On / Date。
- 請統一轉換成 YYYY-MM-DD。
- 不可把 delivery date、ship date、invoice date、due date 當成 po_date。
- 若日期格式為純數字斜線格式（例如 05/11/2024），請先觀察整份文件是否有其他日期格式或語境可判斷：
  - 若文件整體偏向 dd/mm/yyyy，則依 dd/mm/yyyy 解讀
  - 若文件整體偏向 mm/dd/yyyy，則依 mm/dd/yyyy 解讀
- 若同一文件中只有單一歧義日期，且無其他線索可明確判斷，請填 null，不可任意交換月與日。
- 不可因為某一種格式較常見就直接猜測。

3. currency：
- 只根據文件中明確出現的幣別資訊填寫。
- 若文件寫的是 USD、US$、U.S. Dollar，統一輸出 "USD"。
- 若文件寫的是 TWD、NTD、NT$，統一輸出 "TWD"。
- 若文件寫的是 EUR、€, Euro，統一輸出 "EUR"。
- 若文件寫的是 JPY、¥、Yen，統一輸出 "JPY"。
- 若文件沒有明確幣別，填 null。
- 不可根據供應商名稱、公司地區、語言、地址或金額格式猜測幣別。

4. total_amount：
- 提取整份訂單的最終總金額。
- total_amount 必須是代表整份訂單「最終應付金額」或「最終總額」的欄位。
- 不可把 unit price、line amount、subtotal、tax、shipping fee、discount、handling fee 當成 total_amount。
- 若同時出現多個金額欄位，請優先選擇語意上明確表示最終總額的欄位，例如：
  - Total
  - Total Amount
  - Grand Total
  - Final Payable Amount
  - Final Amount
  - Settlement Total
- 若文件中同時出現 subtotal、tax、shipping fee、discount、handling fee 與 final amount，應優先選擇 final amount / final payable amount / grand total 這類最終總額欄位。
- 若沒有明確最終總額，填 null。

5. items：
- 從訂單中的每一筆明細逐筆抽取。
- 每一筆 item 必須對應到文件中的同一列、同一段、或同一筆明細描述。
- 不可把不同 item 的資訊拼接成同一筆。
- 不可把同一筆 item 拆成多筆。
- 若沒有任何明細，輸出空陣列 []。

6. item 欄位規則：
- part_number：
  提取料號 / 產品編號 / Product Code / SKU / Part No. / Item Code / Model No.
- quantity：
  提取數量，輸出整數。
- unit：
  提取單位，例如 pcs、EA、boxes、sets、units；若沒有明確單位則填 null。
- unit_price：
  提取單價，僅保留數字。
- line_amount：
  提取該筆 item 的總金額，僅保留數字。

====================
【複雜 item 特別規則】
====================
1. 文件中的 item 可能以不同形式出現，例如：
- 單行壓縮格式
- 多行分開格式
- 半敘述式句子
- 中英混合標示
- quantity 與 unit 黏寫（例如 18boxes、10pcs）

2. 若 quantity 與 unit 黏在一起，請正確拆開：
- 例如 18boxes -> quantity = 18, unit = boxes
- 例如 10pcs -> quantity = 10, unit = pcs

3. 若某筆 item 以多行表示，請只在能確認屬於同一筆 item 的情況下整合該筆資訊。

4. 若某筆 item 缺少某個欄位，例如缺少 unit 或 line_amount，該欄位填 null，但不要因此丟掉整筆 item。

====================
【中英文混合文件規則】
====================
1. 文件可能同時包含英文與中文欄位或說明文字。
2. 不可因為欄位名稱語言不同就忽略其語意對應。
3. 例如：
- 訂單編號 / 採購單號 可對應 po_number
- 訂單日期 / 日期 可對應 po_date
- 幣別 可對應 currency
- 總金額 / 最終金額 可對應 total_amount
4. 但只有在文件中明確出現時才能填入，不可自行翻譯後猜測不存在的值。

====================
【標準化規則】
====================
1. 日期格式統一為 YYYY-MM-DD。
2. 金額、價格、列總額只保留數字，不要貨幣符號，不要千分位逗號。
3. quantity 請輸出整數。
4. 若欄位值無法由文件內容明確判定，請填 null。
5. 不可為了讓 JSON 更完整而自行猜值。

====================
【Schema】
====================
{json.dumps(schema, ensure_ascii=False, indent=2)}

====================
【訂單內容】
====================
{order_text}
"""
    return prompt

# =========================================================
# 4. LLM 抽取
# =========================================================
def extract_with_llm(order_text: str) -> dict:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "user", "content": build_prompt(order_text)}
        ]
    )

    content = response.choices[0].message.content.strip()

    # 清理可能的 Markdown code fence
    if content.startswith("```json"):
        content = content.replace("```json", "", 1).strip()
    if content.startswith("```"):
        content = content.replace("```", "", 1).strip()
    if content.endswith("```"):
        content = content[:-3].strip()

    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        result = {
            "error": "Invalid JSON",
            "raw_output": content
        }

    return result

# =========================================================
# 5. 檔案抽樣與處理
# =========================================================
def get_sample_files_per_category(sample_size: int = 2) -> list[tuple[str, Path]]:
    """
    每個類別隨機抽取 sample_size 份 txt 檔案。
    回傳格式：
    [
        ("A_field_variation", Path(".../L2_A_001.txt")),
        ...
    ]
    """
    selected_files = []

    for _, folder_name in category_dirs.items():
        category_path = orders_dir / folder_name

        if not category_path.exists():
            print(f"[WARN] Category folder not found: {category_path}")
            continue

        txt_files = sorted([f for f in category_path.iterdir() if f.suffix == ".txt"])

        if not txt_files:
            print(f"[WARN] No txt files found in: {category_path}")
            continue

        if len(txt_files) <= sample_size:
            sampled = txt_files
        else:
            sampled = random.sample(txt_files, sample_size)

        for file_path in sampled:
            selected_files.append((folder_name, file_path))

    return selected_files


def process_files(file_list: list[tuple[str, Path]]) -> None:
    """
    處理抽中的檔案，並依原類別輸出到 results/<experiment>/<category>/ 下。
    若單筆檔案失敗，不中斷整批流程。
    """
    for folder_name, file_path in file_list:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                order_text = f.read()

            # 清理可能造成 request body 異常的特殊字元
            order_text = order_text.replace("\x00", "")
            order_text = "".join(
                ch for ch in order_text
                if ch.isprintable() or ch in "\n\t\r"
            )

            print(f"Processing [{folder_name}] {file_path.name} ...")

            result = extract_with_llm(order_text)

            result_file = file_path.stem + ".json"
            result_path = results_dir / folder_name / result_file
            
            if result_path.exists():
                print(f"[SKIP] Already exists -> {result_path}")
                continue

            with open(result_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            print(f"[OK] Saved -> {result_path}")

        except Exception as e:
            print(f"[ERROR] [{folder_name}] {file_path.name}: {e}")
            continue


# =========================================================
# 6. Main
# =========================================================
def main():
    all_files = []

    for _, folder_name in category_dirs.items():
        category_path = orders_dir / folder_name

        if not category_path.exists():
            print(f"[WARN] Category folder not found: {category_path}")
            continue

        txt_files = sorted([f for f in category_path.iterdir() if f.suffix == ".txt"])

        for file_path in txt_files:
            all_files.append((folder_name, file_path))

    print(f"Total files to process: {len(all_files)}")
    process_files(all_files)


if __name__ == "__main__":
    main()