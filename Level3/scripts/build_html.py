from pathlib import Path
from jinja2 import Environment, FileSystemLoader


# =========================
# 路徑設定
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE_DIR = BASE_DIR / "dataset" / "order_level2_source"
OUTPUT_DIR = BASE_DIR / "dataset" / "order_level3_html"
TEMPLATE_DIR = BASE_DIR / "templates"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# =========================
# 初始化模板
# =========================
env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
template = env.get_template("base_template.html")


def infer_category_from_parent(folder_name: str) -> str:
    """
    根據父資料夾名稱推斷 A~E 類別。

    例如:
    A_field_variation -> A
    B_scattered_fields -> B
    """
    if folder_name.startswith("A_"):
        return "A"
    if folder_name.startswith("B_"):
        return "B"
    if folder_name.startswith("C_"):
        return "C"
    if folder_name.startswith("D_"):
        return "D"
    if folder_name.startswith("E_"):
        return "E"
    return "UNKNOWN"


def render_single_txt(txt_path: Path) -> None:
    """
    將單一 txt 訂單渲染成 HTML。

    參數:
        txt_path: 原始 txt 檔路徑
    """
    # 讀取原始文字內容
    raw_text = txt_path.read_text(encoding="utf-8")

    # 檔名當作 doc_id
    doc_id = txt_path.stem

    # 父資料夾推斷 category
    parent_folder = txt_path.parent.name
    category = infer_category_from_parent(parent_folder)

    # 套模板
    rendered_html = template.render(
        doc_id=doc_id,
        category=category,
        raw_text=raw_text
    )

    # 輸出 HTML
    output_path = OUTPUT_DIR / f"{doc_id}.html"
    output_path.write_text(rendered_html, encoding="utf-8")

    print(f"[OK] HTML generated: {output_path.name}")


def main() -> None:
    """
    遞迴掃描所有子資料夾中的 txt 檔，批次生成 HTML。
    """
    txt_files = sorted(SOURCE_DIR.rglob("*.txt"))

    if not txt_files:
        print("[WARN] No txt files found.")
        return

    print(f"[INFO] Found {len(txt_files)} txt files.")

    for txt_file in txt_files:
        render_single_txt(txt_file)

    print(f"\nDone. Generated {len(txt_files)} HTML files.")


if __name__ == "__main__":
    main()