import os
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

from pathlib import Path
from paddleocr import PaddleOCR


BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "dataset"

TASKS = [
    {
        "name": "clean_resize_70",
        "input_dir": DATASET_DIR / "order_level3_images_clean_resize_70",
        "output_dir": DATASET_DIR / "order_level3_ocr_clean_resize_70"
    },
    {
        "name": "v1_resize_70",
        "input_dir": DATASET_DIR / "order_level3_images_v1_resize_70",
        "output_dir": DATASET_DIR / "order_level3_ocr_v1_resize_70"
    },
    {
        "name": "v2_resize_70",
        "input_dir": DATASET_DIR / "order_level3_images_v2_resize_70",
        "output_dir": DATASET_DIR / "order_level3_ocr_v2_resize_70"
    }
]


def extract_text_from_result(result) -> str:
    """
    從 PaddleOCR 回傳結果中抽取辨識出的文字內容。
    優先抓 rec_texts，若抓不到再 fallback 成字串。
    """
    texts = []

    try:
        for page in result:
            # 情況 1：dict 格式
            if isinstance(page, dict):
                rec_texts = page.get("rec_texts")
                if rec_texts:
                    texts.extend([str(t).strip() for t in rec_texts if str(t).strip()])
                    continue

            # 情況 2：物件格式
            if hasattr(page, "rec_texts"):
                rec_texts = getattr(page, "rec_texts")
                if rec_texts:
                    texts.extend([str(t).strip() for t in rec_texts if str(t).strip()])
                    continue

        # 如果完全抽不到文字，就 fallback
        if not texts:
            texts.append(str(result))

    except Exception as e:
        texts.append(f"[OCR_PARSE_WARNING] {e}")
        texts.append(str(result))

    return "\n".join(texts).strip()


def process_single_image(ocr: PaddleOCR, image_path: Path, output_dir: Path) -> tuple[bool, str]:
    """
    對單張圖片做 OCR 並輸出成 txt。

    回傳:
        (是否成功, 訊息)
    """
    try:
        result = ocr.predict(str(image_path))
        extracted_text = extract_text_from_result(result)

        output_path = output_dir / f"{image_path.stem}.txt"
        output_path.write_text(extracted_text, encoding="utf-8")

        return True, f"[OK] OCR saved: {output_path.name}"

    except Exception as e:
        return False, f"[ERROR] Failed on {image_path.name}: {e}"


def process_task(ocr: PaddleOCR, task: dict) -> None:
    """
    批次處理單一資料夾。
    """
    input_dir = task["input_dir"]
    output_dir = task["output_dir"]
    task_name = task["name"]

    output_dir.mkdir(parents=True, exist_ok=True)

    image_files = []
    for pattern in ("*.png", "*.jpg", "*.jpeg"):
        image_files.extend(input_dir.glob(pattern))
    image_files = sorted(image_files)

    if not image_files:
        print(f"[WARN] No image files found in {input_dir}")
        return

    print(f"\n[INFO] Start OCR task: {task_name}")
    print(f"[INFO] Input : {input_dir}")
    print(f"[INFO] Output: {output_dir}")
    print(f"[INFO] Found {len(image_files)} images")

    success_count = 0
    fail_count = 0

    for idx, image_file in enumerate(image_files, start=1):
        print(f"[INFO] Processing {idx}/{len(image_files)}: {image_file.name}")

        ok, message = process_single_image(ocr, image_file, output_dir)
        print(message)

        if ok:
            success_count += 1
        else:
            fail_count += 1

    print(f"\n[INFO] Finished OCR task: {task_name}")
    print(f"[INFO] Success: {success_count}")
    print(f"[INFO] Failed : {fail_count}")


def main() -> None:
    """
    Level 3 正式 OCR 主流程：
    clean_resize_70 / v1_resize_70 / v2_resize_70
    """
    print("[INFO] Initializing PaddleOCR...")

    ocr = PaddleOCR(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=True
    )

    print("[INFO] PaddleOCR initialized successfully.")

    for task in TASKS:
        process_task(ocr, task)

    print("\n[OK] All OCR tasks completed.")


if __name__ == "__main__":
    main()