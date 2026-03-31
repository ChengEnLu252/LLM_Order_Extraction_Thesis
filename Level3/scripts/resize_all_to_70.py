from pathlib import Path
from PIL import Image


BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "dataset"

# 三組輸入與輸出資料夾
TASKS = [
    {
        "input_dir": DATASET_DIR / "order_level3_images_clean",
        "output_dir": DATASET_DIR / "order_level3_images_clean_resize_70",
        "name": "clean"
    },
    {
        "input_dir": DATASET_DIR / "order_level3_images_v1",
        "output_dir": DATASET_DIR / "order_level3_images_v1_resize_70",
        "name": "v1"
    },
    {
        "input_dir": DATASET_DIR / "order_level3_images_v2",
        "output_dir": DATASET_DIR / "order_level3_images_v2_resize_70",
        "name": "v2"
    }
]

# 正式採用的縮放比例
RESIZE_SCALE = 0.70


def resize_image(image_path: Path, output_path: Path, scale: float) -> None:
    """
    將單張圖片縮放後儲存。

    參數:
        image_path: 原始圖片路徑
        output_path: 輸出圖片路徑
        scale: 縮放比例，例如 0.70
    """
    with Image.open(image_path) as img:
        new_width = int(img.width * scale)
        new_height = int(img.height * scale)

        # 使用高品質縮放方法，避免縮圖後文字變得太糊
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        resized_img.save(output_path)


def process_folder(input_dir: Path, output_dir: Path, group_name: str) -> None:
    """
    批次處理單一資料夾中的所有圖片。
    """
    image_files = []
    for pattern in ("*.png", "*.jpg", "*.jpeg"):
        image_files.extend(input_dir.glob(pattern))
    image_files = sorted(image_files)

    if not image_files:
        print(f"[WARN] No image files found in {input_dir}")
        return

    print(f"\n[INFO] Start resizing group: {group_name}")
    print(f"[INFO] Input : {input_dir}")
    print(f"[INFO] Output: {output_dir}")
    print(f"[INFO] Found {len(image_files)} images")

    success_count = 0
    fail_count = 0

    for idx, image_path in enumerate(image_files, start=1):
        try:
            output_path = output_dir / image_path.name
            resize_image(image_path, output_path, RESIZE_SCALE)

            print(f"[OK] {group_name} {idx}/{len(image_files)}: {image_path.name}")
            success_count += 1

        except Exception as e:
            print(f"[ERROR] {group_name} {idx}/{len(image_files)}: {image_path.name} -> {e}")
            fail_count += 1

    print(f"\n[INFO] Finished group: {group_name}")
    print(f"[INFO] Success: {success_count}")
    print(f"[INFO] Failed : {fail_count}")


def main() -> None:
    """
    將 clean / v1 / v2 三組影像全部縮成 70%。
    """
    print(f"[INFO] Resize scale = {RESIZE_SCALE:.0%}")

    for task in TASKS:
        process_folder(
            input_dir=task["input_dir"],
            output_dir=task["output_dir"],
            group_name=task["name"]
        )

    print("\n[OK] All resize tasks completed.")


if __name__ == "__main__":
    main()