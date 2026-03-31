import os
import json
from openai import OpenAI

# 初始化 OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 設定資料夾
base_dir = os.path.dirname(os.path.abspath(__file__))

orders_dir = os.path.join(base_dir, "dataset", "generated")
results_dir = os.path.join(base_dir, "results")

os.makedirs(results_dir, exist_ok=True)


# 你的 schema（簡化版）
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


# 舊Prompt
#def build_prompt(order_text):
#    prompt = f"""
#你是一個資訊抽取系統。

#請從以下訂單文字中提取資訊，並輸出符合 schema 的 JSON。

#規則：
#1. 只輸出 JSON
#2. 日期統一 YYYY-MM-DD
#3. 金額只保留數字
#4. 若沒有欄位填 null

#Schema:
#{json.dumps(schema, ensure_ascii=False, indent=2)}

#訂單內容：
#{order_text}
#"""

#    return prompt

# 新Prompt
def build_prompt(order_text):
    """
    建立改良版 Prompt（Prompt V2）
    
    設計目標：
    1. 強化欄位定義，避免模型自由發揮
    2. 特別加強 currency 的判讀規則
    3. 強化 items 的逐列對齊要求
    4. 明確規定缺值時要填 null，不可猜測
    5. 限制輸出只能是合法 JSON
    """

    prompt = f"""
你是一個高精度的訂單資訊抽取系統。
你的任務是從訂單文字中擷取關鍵資訊，並輸出成符合指定 schema 的 JSON。

請嚴格遵守以下規則：

【輸出規則】
1. 只能輸出一個合法的 JSON 物件。
2. 不要輸出說明、註解、前言、結尾、Markdown、```json 或任何額外文字。
3. 所有欄位都必須存在於輸出的 JSON 中。
4. 若文件中沒有明確出現某欄位，請填 null。
5. 不可根據常識、幣別習慣、語境或推測自行補值。

【欄位抽取規則】
1. po_number：
   - 提取訂單編號 / 採購單編號 / PO Number。
   - 只能根據文件中明確標示的編號填寫。

2. po_date：
   - 提取訂單日期 / PO Date。
   - 請統一轉換成 YYYY-MM-DD 格式。
   - 若文件中沒有明確日期，填 null。
   - 不可把 delivery date、ship date、invoice date 當成 po_date。

3. currency：
   - 只根據文件中明確出現的幣別資訊填寫。
   - 若文件寫的是 USD、US$、U.S. Dollar，統一輸出 "USD"。
   - 若文件寫的是 TWD、NTD、NT$，統一輸出 "TWD"。
   - 若文件沒有明確寫出幣別，填 null。
   - 不可根據供應商地區、語言、金額格式或其他線索猜測幣別。

4. total_amount：
   - 提取整份訂單的總金額。
   - 只保留數字，輸出為數值型態。
   - 不可把 subtotal、tax、shipping fee 當成 total_amount。
   - 若文件沒有明確總金額，填 null。

5. items：
   - 從訂單中的每一筆明細逐列抽取。
   - 每一筆 item 都必須對應到文件中的同一列或同一筆明細，不可跨列拼接。
   - 不可自行合併不同列資訊。
   - 若沒有任何明細，輸出空陣列 []。

6. item 欄位規則：
   - part_number：提取料號 / 產品編號
   - quantity：提取數量，輸出整數
   - unit：提取單位，例如 pcs、box、set；若無明確單位則填 null
   - unit_price：提取單價，僅保留數字
   - line_amount：提取該列總金額，僅保留數字

【標準化規則】
1. 日期格式統一為 YYYY-MM-DD。
2. 金額與價格只保留數字，不要貨幣符號，不要千分位逗號。
3. quantity 請輸出整數。
4. 若欄位值無法由文件內容明確判定，請填 null，不可猜測。

【Schema】
{json.dumps(schema, ensure_ascii=False, indent=2)}

【訂單內容】
{order_text}
"""
    return prompt


def extract_with_llm(order_text):

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "user", "content": build_prompt(order_text)}
        ]
    )

    content = response.choices[0].message.content.strip()

    # 若模型輸出被 ```json ... ``` 包住，先去掉
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


def main():

    files = sorted([f for f in os.listdir(orders_dir) if f.endswith(".txt")])

    for file in files:

        file_path = os.path.join(orders_dir, file)

        with open(file_path, "r", encoding="utf-8") as f:
            order_text = f.read()

        print(f"Processing {file}...")

        result = extract_with_llm(order_text)

        result_file = file.replace(".txt", ".json")
        result_path = os.path.join(results_dir, result_file)

        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()