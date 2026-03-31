from pathlib import Path
from paddleocr import PaddleOCR


# 請改成你要測試的圖片路徑
IMAGE_PATH = Path("dataset/order_level3_images_clean/L2_A_001.png")


def main() -> None:
    """
    測試單張圖片是否能成功做 OCR。
    """
    if not IMAGE_PATH.exists():
        print(f"[ERROR] Image not found: {IMAGE_PATH}")
        return

    # use_textline_orientation=True 是官方 quick start 會用到的參數風格之一
    ocr = PaddleOCR(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=True
    )

    result = ocr.predict(str(IMAGE_PATH))

    print("========== OCR RESULT ==========")
    print(result)


if __name__ == "__main__":
    main()