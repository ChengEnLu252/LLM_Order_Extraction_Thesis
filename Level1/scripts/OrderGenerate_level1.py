import os
import random
import json
from datetime import datetime, timedelta

# 建立資料夾
base_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(base_dir, "dataset", "generated")

os.makedirs(output_dir, exist_ok=True)

companies = ["承恩科技股份有限公司", "宏達電子有限公司", "華宇半導體", "鼎新材料股份有限公司"]

products = [
    ("TC-24P-001", "Type-C 連接器 24Pin"),
    ("HDMI-21-2M", "HDMI 2.1 高速傳輸線"),
    ("PMIC-A88", "電源管理IC"),
    ("SSD-1TB-X", "固態硬碟 1TB"),
]

units = ["PCS", "個", "顆", "條"]
currencies = ["TWD", "USD"]


def random_date():
    start = datetime(2024, 1, 1)
    random_days = random.randint(0, 600)
    return start + timedelta(days=random_days)


def generate_order(order_id):

    company_buyer = random.choice(companies)
    company_supplier = random.choice(companies)

    date = random_date()
    po_number = f"PO-2026-{order_id:04d}"
    currency = random.choice(currencies)

    num_items = random.randint(1, 4)

    items_text = ""
    total = 0

    items_json = []

    for i in range(num_items):

        part, desc = random.choice(products)
        qty = random.randint(10, 1000)
        price = round(random.uniform(5, 200), 2)

        subtotal = round(qty * price, 2)
        total += subtotal

        unit = random.choice(units)

        items_text += f"{i+1}. {desc} ({part}) 數量: {qty} {unit} 單價: {price} 小計: {subtotal}\n"

        items_json.append({
            "part_number": part,
            "quantity": qty,
            "unit": unit,
            "unit_price": price,
            "line_amount": subtotal
        })

    template_type = random.randint(1, 3)

    if template_type == 1:

        content = f"""
採購單號: {po_number}
日期: {date.strftime('%Y-%m-%d')}
買方: {company_buyer}
賣方: {company_supplier}
幣別: {currency}

明細:
{items_text}

總金額: {round(total,2)}
"""

    elif template_type == 2:

        content = f"""
Subject: {po_number}

Hi,

Please process this order.

Buyer: {company_buyer}
Supplier: {company_supplier}
Date: {date.strftime('%B %d, %Y')}

Items:
{items_text}

Total Amount: {round(total,2)} {currency}
"""

    else:

        roc_year = date.year - 1911

        content = f"""
採購單
單號 {po_number}
日期: 民國{roc_year}年{date.month}月{date.day}日
公司: {company_buyer}

訂購內容:
{items_text}

金額新台幣 {round(total,2)} 元整
"""

    # 建立 ground truth JSON
    order_json = {
        "po_number": po_number,
        "po_date": date.strftime("%Y-%m-%d"),
        "currency": currency,
        "total_amount": round(total, 2),
        "items": items_json
    }

    return content, order_json


# 生成 50 份
for i in range(1, 51):

    content, order_json = generate_order(i)

    txt_path = os.path.join(output_dir, f"po_{i:03d}.txt")
    json_path = os.path.join(output_dir, f"po_{i:03d}.json")

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(content)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(order_json, f, ensure_ascii=False, indent=2)

print("訂單與 Ground Truth JSON 生成完成！")