import json
import random
from pathlib import Path
from datetime import datetime, timedelta


# =========================================================
# Level 2 Dataset Generator
# Thesis: Complex Text Order Documents
# Author: Cheng-En's thesis workflow
# Note:
# - This script generates Level 2 order documents in five categories:
#   A. Field Variation
#   B. Scattered Fields
#   C. Complex Items
#   D. Noise Information
#   E. Mixed Complexity
# - All company names are fictional.
# - Output folder structure is aligned with Level 1 style.
# =========================================================


# =========================================================
# 1. Global Configuration
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

ORDER_DIR = BASE_DIR / "dataset" / "order_level2"
GROUND_TRUTH_DIR = BASE_DIR / "dataset" / "ground_truth_level2"
METADATA_DIR = BASE_DIR / "dataset" / "metadata_level2"

CATEGORY_MAP = {
    "A": "A_field_variation",
    "B": "B_scattered_fields",
    "C": "C_complex_items",
    "D": "D_noise_information",
    "E": "E_mixed_complexity",
}

# 控制隨機性，讓每次生成結果可重現
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# 每類預設要生成的份數
DEFAULT_COUNT_PER_CATEGORY = 5  # 先測試用，正式可改 50

# Level 2 主 schema
SCHEMA_FIELDS = {
    "po_number": "",
    "po_date": "",
    "currency": "",
    "total_amount": "",
    "items": [
        {
            "part_number": "",
            "quantity": "",
            "unit": "",
            "unit_price": "",
            "line_amount": "",
        }
    ],
}

# 虛構公司名稱池（避免使用真實台灣大公司）
COMPANY_NAMES = [
    "Northstar Components Ltd. 北辰元件有限公司",
    "BluePeak Industrial Supply 藍峰工業供應",
    "Vertex Axis Trading 維泰軸心貿易",
    "Silver Oak Procurement 銀橡採購股份有限公司",
    "AuroraLink Systems 極光連結系統",
    "Ironcrest Materials 鐵冠材料有限公司",
    "NovaCircuit Solutions 新曜電路方案",
    "CedarStone Imports 雪松石進出口",
    "Prime Harbor Manufacturing 鼎港製造",
    "OrbitLine Distribution 軌域配銷有限公司"
]

BUYER_NAMES = [
    "Summit Valley Electronics 峰谷電子",
    "Allied Nexus Purchasing 聯合採購中心",
    "BrightCore Assemblies 亮核組裝",
    "GrandRiver Devices 大河裝置",
    "PolarEdge Manufacturing 極鋒製造",
    "Stonepath Industrial 石徑工業",
    "Skyforge Systems 天鑄系統",
    "LumenTrail Procurement 光徑採購"
]

CURRENCIES = ["USD", "EUR", "JPY"]
UNITS = ["pcs", "EA", "boxes", "sets", "units"]

PART_PREFIXES = ["AX", "BK", "CN", "DX", "EV", "FT", "GX", "HM", "IR", "JQ"]
PART_SUFFIXES = ["100", "220", "305", "410", "512", "618", "725", "830", "940"]

REMARKS_POOL = [
    "Please confirm delivery schedule before shipment. 出貨前請先確認交期。",
    "Packaging must comply with export standards. 包裝需符合出口標準。",
    "Partial shipment is not allowed unless approved. 未經同意不得分批出貨。",
    "All goods must match approved specifications. 所有貨品須符合核准規格。",
    "Please include inspection report with shipment. 出貨時請附檢驗報告。"
]

PAYMENT_TERMS_POOL = [
    "Net 30 days（30天付款）",
    "Net 45 days（45天付款）",
    "Payment due upon receipt（收貨後付款）",
    "30% advance, 70% before shipment（30% 預付，70% 出貨前付清）",
]

SHIPPING_TERMS_POOL = [
    "FOB Origin（離岸交貨）",
    "CIF Destination（成本保險加運費）",
    "EXW Warehouse（工廠交貨）",
    "DAP Customer Site（目的地交貨）",
]

FIELD_ALIASES = {
    "po_number": ["PO Number", "P.O. No.", "Purchase Order No.", "Order Ref", "Order ID"],
    "po_date": ["PO Date", "Order Date", "Date Issued", "Issued On", "Date"],
    "currency": ["Currency", "Curr.", "Settlement Currency", "Billing Currency"],
    "total_amount": ["Total", "Grand Total", "Total Amount", "Amount Due", "Final Amount"],
    "part_number": ["Part No.", "Item Code", "Product Code", "SKU", "Model No."],
    "quantity": ["Qty", "Quantity", "Order Qty", "Units Ordered"],
    "unit": ["Unit", "UOM", "Measure", "Unit Type"],
    "unit_price": ["Unit Price", "Price/Unit", "Item Price", "Rate"],
    "line_amount": ["Amount", "Line Total", "Extended Price", "Total Price"],
}

CONTACT_NAMES = [
    "Melissa Turner / 王美玲",
    "Daniel Brooks / 陳志宏",
    "Sophia Lin / 林雅婷",
    "Kevin Huang / 黃建凱",
    "Ivy Chen / 陳怡君"
]


# =========================================================
# 2. Utility Functions
# =========================================================

def ensure_directories() -> None:
    """
    建立所有需要的輸出資料夾。
    """
    for category_name in CATEGORY_MAP.values():
        (ORDER_DIR / category_name).mkdir(parents=True, exist_ok=True)
        (GROUND_TRUTH_DIR / category_name).mkdir(parents=True, exist_ok=True)
        (METADATA_DIR / category_name).mkdir(parents=True, exist_ok=True)


def random_date(start_year: int = 2024, end_year: int = 2026) -> str:
    """
    隨機生成日期，並統一 ground truth 使用 YYYY-MM-DD。
    """
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    delta_days = (end_date - start_date).days
    chosen = start_date + timedelta(days=random.randint(0, delta_days))
    return chosen.strftime("%Y-%m-%d")


def random_date_variant(date_str: str) -> str:
    """
    將標準日期轉成不同文件表現形式，用於 Level 2 增加表達變異。
    """
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    variants = [
        dt.strftime("%Y-%m-%d"),
        dt.strftime("%d/%m/%Y"),
        dt.strftime("%m/%d/%Y"),
        dt.strftime("%d %b %Y"),
        dt.strftime("%B %d, %Y"),
    ]
    return random.choice(variants)


def random_po_number() -> str:
    """
    生成隨機 PO 編號。
    """
    year = random.choice(["2024", "2025", "2026"])
    serial = random.randint(1000, 9999)
    return f"PO-{year}-{serial}"


def random_company_name() -> str:
    return random.choice(COMPANY_NAMES)


def random_buyer_name() -> str:
    return random.choice(BUYER_NAMES)


def random_currency() -> str:
    return random.choice(CURRENCIES)


def random_part_number() -> str:
    return f"{random.choice(PART_PREFIXES)}-{random.choice(PART_SUFFIXES)}"


def random_quantity() -> int:
    return random.randint(2, 40)


def random_unit() -> str:
    return random.choice(UNITS)


def random_unit_price() -> float:
    return round(random.uniform(2.0, 100.0), 2)


def format_money(value: float) -> str:
    """
    金額統一保留兩位小數。
    """
    return f"{value:.2f}"


def generate_items(min_items: int = 2, max_items: int = 5) -> list:
    """
    生成標準化 items 結構，這是所有類型共用的底層資料來源。
    """
    item_count = random.randint(min_items, max_items)
    items = []

    for _ in range(item_count):
        quantity = random_quantity()
        unit_price = random_unit_price()
        line_amount = round(quantity * unit_price, 2)

        item = {
            "part_number": random_part_number(),
            "quantity": quantity,
            "unit": random_unit(),
            "unit_price": unit_price,
            "line_amount": line_amount,
        }
        items.append(item)

    return items


def build_base_order_data() -> dict:
    """
    先建立一份標準化訂單資料，再由 A~E 類函式把它渲染成不同文字風格。
    """
    po_number = random_po_number()
    po_date = random_date()
    currency = random_currency()
    supplier = random_company_name()
    buyer = random_buyer_name()
    items = generate_items()

    total_amount = round(sum(item["line_amount"] for item in items), 2)

    return {
        "po_number": po_number,
        "po_date": po_date,
        "currency": currency,
        "supplier_name": supplier,
        "buyer_name": buyer,
        "total_amount": total_amount,
        "items": items,
        "remark": random.choice(REMARKS_POOL),
        "payment_terms": random.choice(PAYMENT_TERMS_POOL),
        "shipping_terms": random.choice(SHIPPING_TERMS_POOL),
    }


def build_ground_truth(base_data: dict) -> dict:
    """
    根據 base_data 建立標準化 ground truth。
    注意：只保留論文主 schema 所需欄位。
    """
    return {
        "po_number": base_data["po_number"],
        "po_date": base_data["po_date"],
        "currency": base_data["currency"],
        "total_amount": format_money(base_data["total_amount"]),
        "items": [
            {
                "part_number": item["part_number"],
                "quantity": item["quantity"],
                "unit": item["unit"],
                "unit_price": format_money(item["unit_price"]),
                "line_amount": format_money(item["line_amount"]),
            }
            for item in base_data["items"]
        ],
    }


def pick_alias(field_name: str) -> str:
    """
    從欄位別名池中隨機挑一個名稱。
    """
    return random.choice(FIELD_ALIASES[field_name])


def save_text_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def save_json_file(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# =========================================================
# 3. Render Functions for Category A ~ E
# =========================================================

def render_category_A(base_data: dict) -> tuple[str, None]:
    """
    A 類：欄位名稱變異型
    核心特色：
    - 使用不同欄位別名
    - 文件整體仍相對整齊
    - 加入 easy / medium / hard 難度分層
    """

    # A 類專用：避免 total 欄位名稱太像 D/E 類
    a_total_aliases = ["Total", "Total Amount", "Grand Total"]

    # A 類難度分層
    difficulty = random.choices(
        ["easy", "medium", "hard"],
        weights=[0.4, 0.4, 0.2],
        k=1
    )[0]

    # 先設定預設欄位名稱（作為 easy 時的保守版本）
    po_label = "PO Number"
    date_label = "PO Date"
    currency_label = "Currency"
    total_label = random.choice(a_total_aliases)

    part_label = "Part No."
    qty_label = "Quantity"
    unit_label = "Unit"
    unit_price_label = "Unit Price"
    amount_label = "Line Total"

    # ===== 根據難度決定要變多少欄位 =====
    if difficulty == "easy":
        # header 變 2~3 個，item 變 1~2 個
        header_candidates = ["po_number", "po_date", "currency"]
        item_candidates = ["part_number", "quantity", "unit", "unit_price", "line_amount"]

        selected_headers = random.sample(header_candidates, k=random.randint(2, 3))
        selected_items = random.sample(item_candidates, k=random.randint(1, 2))

    elif difficulty == "medium":
        # header 幾乎全變，item 變 3~4 個
        selected_headers = ["po_number", "po_date", "currency"]
        item_candidates = ["part_number", "quantity", "unit", "unit_price", "line_amount"]
        selected_items = random.sample(item_candidates, k=random.randint(3, 4))

    else:  # hard
        # header 全變，item 全變
        selected_headers = ["po_number", "po_date", "currency"]
        selected_items = ["part_number", "quantity", "unit", "unit_price", "line_amount"]

    # ===== 套用 alias =====
    if "po_number" in selected_headers:
        po_label = pick_alias("po_number")
    if "po_date" in selected_headers:
        date_label = pick_alias("po_date")
    if "currency" in selected_headers:
        currency_label = pick_alias("currency")

    if "part_number" in selected_items:
        part_label = pick_alias("part_number")
    if "quantity" in selected_items:
        qty_label = pick_alias("quantity")
    if "unit" in selected_items:
        unit_label = pick_alias("unit")
    if "unit_price" in selected_items:
        unit_price_label = pick_alias("unit_price")
    if "line_amount" in selected_items:
        amount_label = pick_alias("line_amount")

    # ===== 組裝文件 =====
    lines = []
    lines.append(f"Supplier: {base_data['supplier_name']}")
    lines.append(f"Buyer: {base_data['buyer_name']}")
    lines.append(f"{po_label}: {base_data['po_number']}")
    lines.append(f"{date_label}: {random_date_variant(base_data['po_date'])}")
    lines.append(f"{currency_label}: {base_data['currency']}")
    lines.append("")
    lines.append(
        f"{part_label:<15} {qty_label:<12} {unit_label:<10} "
        f"{unit_price_label:<15} {amount_label:<15}"
    )

    for item in base_data["items"]:
        lines.append(
            f"{item['part_number']:<15} "
            f"{item['quantity']:<12} "
            f"{item['unit']:<10} "
            f"{format_money(item['unit_price']):<15} "
            f"{format_money(item['line_amount']):<15}"
        )

    lines.append("")
    lines.append(f"{total_label}: {format_money(base_data['total_amount'])}")
    lines.append(f"Remarks: {base_data['remark']}")

    return "\n".join(lines), None


def render_category_B(base_data: dict) -> tuple[str, None]:
    """
    B 類：欄位分散型
    核心特色：
    - 核心欄位分散在不同段落與句子中
    - 不使用固定欄位標籤格式
    - item 區塊仍可讀，但不完全固定同一模板
    """

    difficulty = random.choices(
        ["easy", "medium", "hard"],
        weights=[0.35, 0.45, 0.20],
        k=1
    )[0]

    total_phrases = [
        "Amount due upon confirmation",
        "Final payable amount",
        "Total amount for this order",
        "Settlement total"
    ]
    total_label = random.choice(total_phrases)

    intro_templates = [
        "Please arrange the following materials for our upcoming production schedule.",
        "Kindly process the following order items for our current purchasing request.",
        "Please prepare the materials listed below for the next production batch."
    ]
    intro_text = random.choice(intro_templates)

    po_templates = [
        f"The official reference for this order is {base_data['po_number']}.",
        f"For tracking purposes, please use order reference {base_data['po_number']}.",
        f"This request should be recorded under reference number {base_data['po_number']}."
    ]
    po_text = random.choice(po_templates)

    date_templates = [
        f"This order was issued on {random_date_variant(base_data['po_date'])}.",
        f"The issuance date for this order is {random_date_variant(base_data['po_date'])}.",
        f"Please note that the order date is {random_date_variant(base_data['po_date'])}."
    ]
    date_text = random.choice(date_templates)

    currency_templates = [
        f"All prices are stated in {base_data['currency']}.",
        f"The transaction currency for this order is {base_data['currency']}.",
        f"Please process all item prices in {base_data['currency']}."
    ]
    currency_text = random.choice(currency_templates)

    item_templates = ["style_1", "style_2", "style_3"]

    lines = []

    if difficulty == "easy":
        lines.append(f"Supplier: {base_data['supplier_name']}")
        lines.append(f"Buyer: {base_data['buyer_name']}")
        lines.append("")
        lines.append(intro_text)
        lines.append(po_text)
        lines.append("")
        lines.append("Item List:")

    elif difficulty == "medium":
        lines.append(intro_text)
        lines.append("")
        lines.append(f"Supplier information: {base_data['supplier_name']}")
        lines.append(po_text)
        lines.append("")
        lines.append(f"Requested by: {base_data['buyer_name']}")
        lines.append("")
        lines.append("Ordered Materials:")

    else:  # hard
        lines.append("Procurement Note:")
        lines.append(intro_text)
        lines.append("")
        lines.append(f"Requested by purchasing team: {base_data['buyer_name']}")
        lines.append("")
        lines.append("Supplier Details:")
        lines.append(base_data['supplier_name'])
        lines.append("")
        lines.append(po_text)
        lines.append("")
        lines.append("Materials Requested:")

    for idx, item in enumerate(base_data["items"], start=1):
        item_style = random.choice(item_templates)

        if item_style == "style_1":
            lines.append(
                f"{idx}. Part {item['part_number']} / Qty {item['quantity']} {item['unit']} "
                f"/ Unit Price {format_money(item['unit_price'])} / Amount {format_money(item['line_amount'])}"
            )
        elif item_style == "style_2":
            lines.append(
                f"{idx}. {item['part_number']}, quantity {item['quantity']} {item['unit']}, "
                f"unit price {format_money(item['unit_price'])}, amount {format_money(item['line_amount'])}"
            )
        else:
            lines.append(
                f"{idx}. Part: {item['part_number']} | Qty: {item['quantity']} {item['unit']} | "
                f"Price: {format_money(item['unit_price'])} | Amount: {format_money(item['line_amount'])}"
            )

    lines.append("")

    if difficulty == "easy":
        lines.append(date_text)
        lines.append(currency_text)
        lines.append(f"Payment Terms: {base_data['payment_terms']}")
        lines.append(f"Shipping Terms: {base_data['shipping_terms']}")
        lines.append("")
        lines.append(f"{total_label}: {format_money(base_data['total_amount'])}")
        lines.append(f"Remark: {base_data['remark']}")

    elif difficulty == "medium":
        lines.append(f"Payment Terms: {base_data['payment_terms']}")
        lines.append(date_text)
        lines.append("")
        lines.append(f"Shipping arrangement follows {base_data['shipping_terms']}.")
        lines.append(currency_text)
        lines.append("")
        lines.append(f"{total_label}: {format_money(base_data['total_amount'])}")
        lines.append(f"Additional note: {base_data['remark']}")

    else:  # hard
        lines.append(date_text)
        lines.append("")
        lines.append(f"The agreed payment condition is {base_data['payment_terms']}.")
        lines.append(f"Delivery will follow {base_data['shipping_terms']}.")
        lines.append(currency_text)
        lines.append("")
        lines.append(f"{total_label}: {format_money(base_data['total_amount'])}")
        lines.append(f"Please note: {base_data['remark']}")

    return "\n".join(lines), None

def render_category_C(base_data: dict) -> tuple[str, None]:
    """
    C 類：items 複雜型
    核心特色：
    - items 不是整齊表格
    - 混合單行、跨行、半敘述式表達
    - 加入 easy / medium / hard 難度分層
    """

    difficulty = random.choices(
        ["easy", "medium", "hard"],
        weights=[0.30, 0.45, 0.25],
        k=1
    )[0]

    lines = []
    lines.append(f"PO Number: {base_data['po_number']}")
    lines.append(f"PO Date: {random_date_variant(base_data['po_date'])}")
    lines.append(f"Currency: {base_data['currency']}")
    lines.append(f"Supplier: {base_data['supplier_name']}")
    lines.append("")
    lines.append("Ordered Items:")

    # C 類 item style 池
    all_styles = [
        "single_line_compact",   # AX-220 / 10pcs / 5.00 / 50.00
        "multi_line",            # Part No / Qty / Unit Price / Amount
        "semi_narrative",        # Item AX-220, ordered quantity ...
        "pipe_style",            # Part: AX-220 | Qty: 10 pcs | Price: 5.00 | Amount: 50.00
        "qty_first_style"        # Qty 10 pcs of AX-220 at 5.00 each, total 50.00
    ]

    # 根據難度決定 style 使用範圍
    if difficulty == "easy":
        allowed_styles = ["single_line_compact", "multi_line", "semi_narrative"]
    elif difficulty == "medium":
        allowed_styles = ["single_line_compact", "multi_line", "semi_narrative", "pipe_style"]
    else:  # hard
        allowed_styles = all_styles

    # hard 時盡量確保同一份文件內至少混到 3 種 style
    chosen_styles = []
    if difficulty == "hard" and len(base_data["items"]) >= 3:
        chosen_styles = random.sample(allowed_styles, k=3)
        while len(chosen_styles) < len(base_data["items"]):
            chosen_styles.append(random.choice(allowed_styles))
        random.shuffle(chosen_styles)

    for idx, item in enumerate(base_data["items"], start=1):
        if chosen_styles:
            style = chosen_styles[idx - 1]
        else:
            style = random.choice(allowed_styles)

        if style == "single_line_compact":
            qty_unit = random.choice([
                f"{item['quantity']}{item['unit']}",
                f"{item['quantity']} {item['unit']}"
            ])
            lines.append(
                f"{idx}) {item['part_number']} / {qty_unit} / "
                f"{format_money(item['unit_price'])} / {format_money(item['line_amount'])}"
            )

        elif style == "multi_line":
            lines.append(f"{idx}) Part No: {item['part_number']}")
            lines.append(f"   Qty: {item['quantity']} {item['unit']}")
            lines.append(f"   Unit Price: {format_money(item['unit_price'])}")
            lines.append(f"   Amount: {format_money(item['line_amount'])}")

        elif style == "semi_narrative":
            lines.append(
                f"{idx}) Item {item['part_number']}, ordered quantity {item['quantity']} {item['unit']}, "
                f"unit price {format_money(item['unit_price'])}, total {format_money(item['line_amount'])}"
            )

        elif style == "pipe_style":
            lines.append(
                f"{idx}) Part: {item['part_number']} | Qty: {item['quantity']} {item['unit']} | "
                f"Price: {format_money(item['unit_price'])} | Amount: {format_money(item['line_amount'])}"
            )

        else:  # qty_first_style
            lines.append(
                f"{idx}) Qty {item['quantity']} {item['unit']} of {item['part_number']} "
                f"at {format_money(item['unit_price'])} each, total {format_money(item['line_amount'])}"
            )

    lines.append("")
    lines.append(f"Grand Total: {format_money(base_data['total_amount'])}")
    lines.append(f"Remark: {base_data['remark']}")

    return "\n".join(lines), None


def render_category_D(base_data: dict) -> tuple[str, float]:
    """
    D 類：干擾資訊型
    核心特色：
    - subtotal / tax / shipping / contact / address 等干擾資訊
    - 但仍存在正確 total_amount
    """
    subtotal = round(sum(item["line_amount"] for item in base_data["items"]), 2)
    tax = round(subtotal * 0.05, 2)
    shipping_fee = round(random.uniform(10.0, 80.0), 2)
    final_payable_amount = round(subtotal + tax + shipping_fee, 2)
    
    # 注意：
    # 為了不破壞主 schema 的一致性，
    # 這裡的 subtotal/tax/shipping/grand_total 只是文件干擾訊息。
    lines = []
    lines.append(f"Purchase Order No.: {base_data['po_number']}")
    lines.append(f"Date: {random_date_variant(base_data['po_date'])}")
    lines.append(f"Billing Currency: {base_data['currency']}")
    lines.append(f"Supplier: {base_data['supplier_name']}")
    lines.append(f"Buyer: {base_data['buyer_name']}")
    lines.append("")
    lines.append("Ship To: 18 North Avenue, West District")
    lines.append(f"Contact Person: {random.choice(CONTACT_NAMES)}")
    lines.append("Telephone: +1-555-0179")
    lines.append("Email: orders@procurement-mail.test")
    lines.append("")

    lines.append("Items:")
    for item in base_data["items"]:
        lines.append(
            f"- {item['part_number']} | Qty {item['quantity']} {item['unit']} | "
            f"Price {format_money(item['unit_price'])} | Amount {format_money(item['line_amount'])}"
        )

    lines.append("")
    lines.append(f"Subtotal: {format_money(subtotal)}")
    lines.append(f"Tax: {format_money(tax)}")
    lines.append(f"Shipping Fee: {format_money(shipping_fee)}")
    lines.append(f"Final Payable Amount: {format_money(final_payable_amount)}")
    lines.append(f"Payment Terms: {base_data['payment_terms']}")
    lines.append(f"Shipping Terms: {base_data['shipping_terms']}")
    lines.append(f"Remark: {base_data['remark']}")

    return "\n".join(lines), final_payable_amount


def render_category_E(base_data: dict) -> tuple[str, float]:
    """
    E 類：混合型
    核心特色：
    - 同時包含欄位名稱變異、資訊分散、複雜 items、干擾資訊
    - ground truth 的 total_amount 以 Final Amount 為準
    """

    difficulty = random.choices(
        ["easy", "medium", "hard"],
        weights=[0.25, 0.45, 0.30],
        k=1
    )[0]

    po_label = pick_alias("po_number")
    date_label = pick_alias("po_date")

    subtotal = round(sum(item["line_amount"] for item in base_data["items"]), 2)
    discount = round(random.uniform(5.0, 20.0), 2)
    handling_fee = round(random.uniform(3.0, 15.0), 2)
    final_amount = round(subtotal - discount + handling_fee, 2)

    lines = []
    lines.append(f"Supplier: {base_data['supplier_name']}")
    lines.append(f"Buyer: {base_data['buyer_name']}")
    lines.append("")

    intro_templates = [
        "Please process the following materials based on our current procurement request.",
        "Kindly proceed with the following mixed-format order details.",
        "Please review and process the following procurement request."
    ]
    lines.append(random.choice(intro_templates))
    lines.append(f"{po_label}: {base_data['po_number']}")
    lines.append("")

    if difficulty == "easy":
        lines.append("The requested items are listed below.")
    elif difficulty == "medium":
        lines.append("The requested materials are summarized below in mixed item formats.")
    else:
        lines.append("Please note that the requested items are presented in different line formats below.")

    lines.append("")

    item_styles = ["mixed_1", "mixed_2", "mixed_3", "mixed_4"]

    for idx, item in enumerate(base_data["items"], start=1):
        style = random.choice(item_styles)

        if style == "mixed_1":
            lines.append(
                f"{idx}. {item['part_number']} / ordered quantity {item['quantity']}{item['unit']} / "
                f"rate {format_money(item['unit_price'])} / line total {format_money(item['line_amount'])}"
            )

        elif style == "mixed_2":
            lines.append(f"{idx}. Product Code: {item['part_number']}")
            lines.append(f"   Units Ordered: {item['quantity']} {item['unit']}")
            lines.append(f"   Item Price: {format_money(item['unit_price'])}")
            lines.append(f"   Amount: {format_money(item['line_amount'])}")

        elif style == "mixed_3":
            lines.append(
                f"{idx}. Part: {item['part_number']} | Qty: {item['quantity']} {item['unit']} | "
                f"Price: {format_money(item['unit_price'])} | Amount: {format_money(item['line_amount'])}"
            )

        else:  # mixed_4
            lines.append(
                f"{idx}. Qty {item['quantity']} {item['unit']} of {item['part_number']} "
                f"at {format_money(item['unit_price'])} each, total {format_money(item['line_amount'])}"
            )

    lines.append("")
    lines.append("Additional Information:")
    lines.append(f"{date_label}: {random_date_variant(base_data['po_date'])}")

    if difficulty == "easy":
        lines.append(f"Payment Terms: {base_data['payment_terms']}")
        lines.append(f"Shipping Terms: {base_data['shipping_terms']}")
    elif difficulty == "medium":
        lines.append(f"The agreed payment condition is {base_data['payment_terms']}.")
        lines.append(f"Delivery arrangement follows {base_data['shipping_terms']}.")
    else:
        lines.append(f"Payment for this order shall follow {base_data['payment_terms']}.")
        lines.append(f"Shipping arrangement will follow {base_data['shipping_terms']}.")

    lines.append(f"All prices are quoted in {base_data['currency']}.")
    lines.append(f"Subtotal: {format_money(subtotal)}")
    lines.append(f"Discount: {format_money(discount)}")
    lines.append(f"Handling Fee: {format_money(handling_fee)}")
    lines.append(f"Final Amount: {format_money(final_amount)}")
    lines.append(f"Remark: {base_data['remark']}")

    return "\n".join(lines), final_amount


# =========================================================
# 4. Metadata Builder
# =========================================================

def build_metadata(doc_id: str, category_code: str, base_data: dict) -> dict:
    category_name_lookup = {
        "A": "field_variation",
        "B": "scattered_fields",
        "C": "complex_items",
        "D": "noise_information",
        "E": "mixed_complexity",
    }

    complexity_map = {
        "A": ["field_variation"],
        "B": ["scattered_fields"],
        "C": ["complex_items"],
        "D": ["noise_information"],
        "E": ["field_variation", "scattered_fields", "complex_items", "noise_information"],
    }

    difficulty = random.choice(["easy", "medium", "hard"]) if category_code != "E" else random.choice(["medium", "hard"])

    return {
        "doc_id": doc_id,
        "level": "level2",
        "category": category_code,
        "category_name": category_name_lookup[category_code],
        "difficulty": difficulty,
        "complexity_type": complexity_map[category_code],
        "item_count": len(base_data["items"]),
        "currency": base_data["currency"],
        "language_style": "bilingual",
        "target_total_source": "direct_total" if category_code in ["A", "B", "C"] else "computed_final_amount",
        "generator_version": "v1"
    }


# =========================================================
# 5. Generation Controller
# =========================================================

def render_by_category(category_code: str, base_data: dict) -> str:
    """
    依據類型代碼呼叫對應渲染函式。
    """
    if category_code == "A":
        return render_category_A(base_data)
    elif category_code == "B":
        return render_category_B(base_data)
    elif category_code == "C":
        return render_category_C(base_data)
    elif category_code == "D":
        return render_category_D(base_data)
    elif category_code == "E":
        return render_category_E(base_data)
    else:
        raise ValueError(f"Unsupported category code: {category_code}")


def generate_category_dataset(category_code: str, count: int) -> None:
    """
    為指定類別生成 count 份文件。
    """
    category_folder_name = CATEGORY_MAP[category_code]

    for i in range(1, count + 1):
        doc_id = f"L2_{category_code}_{i:03d}"

        # 1. 先建立標準化資料
        base_data = build_base_order_data()

        # 2. 建立 ground truth
        ground_truth = build_ground_truth(base_data)

        # 3. 依照類型渲染成不同文字文件
        order_text, updated_total_amount = render_by_category(category_code, base_data)
        
        if updated_total_amount is not None:
            ground_truth["total_amount"] = format_money(updated_total_amount)

        # 4. 建立 metadata
        metadata = build_metadata(doc_id, category_code, base_data)

        # 5. 輸出檔案路徑
        order_path = ORDER_DIR / category_folder_name / f"{doc_id}.txt"
        gt_path = GROUND_TRUTH_DIR / category_folder_name / f"{doc_id}.json"
        meta_path = METADATA_DIR / category_folder_name / f"{doc_id}.json"

        # 6. 存檔
        save_text_file(order_path, order_text)
        save_json_file(gt_path, ground_truth)
        save_json_file(meta_path, metadata)

        print(f"[OK] Generated {doc_id}")


def generate_level2_dataset(count_per_category: int = DEFAULT_COUNT_PER_CATEGORY) -> None:
    """
    一次生成 Level 2 全部 A~E 類資料。
    """
    ensure_directories()

    for category_code in CATEGORY_MAP.keys():
        print(f"\n=== Generating Category {category_code}: {CATEGORY_MAP[category_code]} ===")
        generate_category_dataset(category_code, count_per_category)

    print("\nAll Level 2 documents generated successfully.")


# =========================================================
# 6. Main
# =========================================================

if __name__ == "__main__":
    # 先用小量測試，確認格式都正常後，再改成 50
    generate_level2_dataset(count_per_category=50)