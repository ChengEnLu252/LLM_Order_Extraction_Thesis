import os
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

import time
from pathlib import Path
from paddleocr import PaddleOCR


BASE_DIR = Path(__file__).resolve().parent.parent

# 先測原圖，再改成 80%、70%
INPUT_DIR = BASE_DIR / "dataset" / "order_level3_images_clean_resize_70"
OUTPUT_DIR = BASE_DIR / "dataset" / "order_level3_ocr_clean_resize_70"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def extract_text_from_result(result) -> str:
    """
    從 PaddleOCR 回傳結果中抽取文字。
    """
    texts = []

    try:
        for page in result:
            if isinstance(page, dict):
                rec_texts = page.get("rec_texts")
                if rec_texts:
                    texts.extend([str(t).strip() for t in rec_texts if str(t).strip()])
                    continue

            if hasattr(page, "rec_texts"):
                rec_texts = getattr(page, "rec_texts")
                if rec_texts:
                    texts.extend([str(t).strip() for t in rec_texts if str(t).strip()])
                    continue

        if not texts:
            texts.append(str(result))

    except Exception as e:
        texts.append(f"[OCR_PARSE_WARNING] {e}")
        texts.append(str(result))

    return "\n".join(texts).strip()


def process_single_image(ocr: PaddleOCR, image_path: Path) -> tuple[bool, float, str]:
    """
    對單張圖片做 OCR，回傳:
    - 是否成功
    - 花費秒數
    - 訊息
    """
    try:
        start_time = time.time()

        result = ocr.predict(str(image_path))
        extracted_text = extract_text_from_result(result)

        output_path = OUTPUT_DIR / f"{image_path.stem}.txt"
        output_path.write_text(extracted_text, encoding="utf-8")

        elapsed = time.time() - start_time
        return True, elapsed, f"[OK] OCR saved: {output_path.name}"

    except Exception as e:
        elapsed = time.time() - start_time
        return False, elapsed, f"[ERROR] Failed on {image_path.name}: {e}"


def main() -> None:
    """
    批次 OCR + 計時。
    """
    image_files = []
    for pattern in ("*.png", "*.jpg", "*.jpeg"):
        image_files.extend(INPUT_DIR.glob(pattern))
    image_files = sorted(image_files)

    if not image_files:
        print(f"[WARN] No image files found in {INPUT_DIR}")
        return

    print(f"[INFO] Found {len(image_files)} images in {INPUT_DIR}")
    print("[INFO] Initializing OCR...")

    init_start = time.time()
    ocr = PaddleOCR(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=True
    )
    init_elapsed = time.time() - init_start

    print(f"[INFO] OCR initialized successfully in {init_elapsed:.2f} sec")

    success_count = 0
    fail_count = 0
    total_predict_time = 0.0

    for idx, image_file in enumerate(image_files, start=1):
        print(f"\n[INFO] Processing {idx}/{len(image_files)}: {image_file.name}")

        ok, elapsed, message = process_single_image(ocr, image_file)
        print(message)
        print(f"[INFO] Predict time: {elapsed:.2f} sec")

        total_predict_time += elapsed

        if ok:
            success_count += 1
        else:
            fail_count += 1

    avg_time = total_predict_time / len(image_files)

    print("\n[INFO] OCR batch completed.")
    print(f"[INFO] Success: {success_count}")
    print(f"[INFO] Failed : {fail_count}")
    print(f"[INFO] Total predict time: {total_predict_time:.2f} sec")
    print(f"[INFO] Average per image : {avg_time:.2f} sec")


if __name__ == "__main__":
    main()