from pathlib import Path
import json
import random

import cv2
import numpy as np


# =========================
# 路徑設定
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent
CLEAN_DIR = BASE_DIR / "dataset" / "order_level3_images_clean"
V1_DIR = BASE_DIR / "dataset" / "order_level3_images_v1"
V2_DIR = BASE_DIR / "dataset" / "order_level3_images_v2"
META_DIR = BASE_DIR / "dataset" / "metadata_level3"

V1_DIR.mkdir(parents=True, exist_ok=True)
V2_DIR.mkdir(parents=True, exist_ok=True)
META_DIR.mkdir(parents=True, exist_ok=True)


# =========================
# 基本工具函式
# =========================
def infer_category_from_doc_id(doc_id: str) -> str:
    """
    根據檔名推斷 A~E 類別。
    例如:
        L2_A_001 -> A
        L2_B_023 -> B
    """
    parts = doc_id.split("_")
    if len(parts) >= 2:
        return parts[1]
    return "UNKNOWN"


def load_image_cv(path: Path) -> np.ndarray:
    """
    使用 OpenCV 讀取影像。
    """
    img = cv2.imread(str(path))
    if img is None:
        raise ValueError(f"Cannot read image: {path}")
    return img


def save_image_cv(path: Path, img: np.ndarray) -> None:
    """
    使用 OpenCV 儲存影像。
    """
    success = cv2.imwrite(str(path), img)
    if not success:
        raise ValueError(f"Failed to save image: {path}")


# =========================
# 影像處理函式
# =========================
def apply_low_resolution(img: np.ndarray, scale: float) -> np.ndarray:
    """
    先縮小再放大，模擬解析度下降。
    scale 越小，畫質越差。
    """
    h, w = img.shape[:2]

    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))

    small = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    restored = cv2.resize(small, (w, h), interpolation=cv2.INTER_LINEAR)
    return restored


def apply_blur(img: np.ndarray, kernel_size: int) -> np.ndarray:
    """
    套用 Gaussian Blur。
    kernel_size 必須是奇數，例如 3、5。
    """
    return cv2.GaussianBlur(img, (kernel_size, kernel_size), 0)


def apply_rotation(img: np.ndarray, angle: float) -> np.ndarray:
    """
    輕微旋轉影像，空白區域補白色。
    """
    h, w = img.shape[:2]
    center = (w // 2, h // 2)

    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        img,
        matrix,
        (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255)
    )
    return rotated


def apply_noise(img: np.ndarray, sigma: float) -> np.ndarray:
    """
    加入高斯雜訊。
    sigma 越大，噪聲越明顯。
    """
    noise = np.random.normal(0, sigma, img.shape).astype(np.float32)
    noisy = img.astype(np.float32) + noise
    noisy = np.clip(noisy, 0, 255).astype(np.uint8)
    return noisy


def apply_shadow(img: np.ndarray, x_start: float, y_start: float) -> np.ndarray:
    """
    疊加輕微亮度不均效果。
    x_start, y_start 越小，陰影越明顯。
    """
    h, w = img.shape[:2]

    x = np.linspace(x_start, 1.0, w)
    y = np.linspace(y_start, 1.0, h)
    mask = np.outer(y, x)

    shadowed = img.astype(np.float32)
    for c in range(3):
        shadowed[:, :, c] *= mask

    shadowed = np.clip(shadowed, 0, 255).astype(np.uint8)
    return shadowed


# =========================
# v1 / v2 生成函式
# =========================
def generate_v1(img: np.ndarray) -> tuple[np.ndarray, dict]:
    """
    v1: 輕度退化版
    目標：
    - 肉眼可辨識與 clean 不同
    - 但仍然屬於高品質文件影像
    - OCR 應該仍大多能正確辨識

    處理內容：
    1. 輕微降解析度
    2. 輕微模糊
    3. 輕微亮度不均
    """
    metadata = {}

    # 1. 輕微降解析度
    scale = random.choice([0.88, 0.90, 0.92])
    img = apply_low_resolution(img, scale=scale)
    metadata["resolution_scale"] = scale

    # 2. 輕微模糊
    blur_kernel = 3
    img = apply_blur(img, kernel_size=blur_kernel)
    metadata["blur_kernel"] = blur_kernel

    # 3. 輕微亮度不均
    x_start = random.choice([0.96, 0.97])
    y_start = random.choice([0.97, 0.98])
    img = apply_shadow(img, x_start=x_start, y_start=y_start)
    metadata["shadow"] = True
    metadata["shadow_x_start"] = x_start
    metadata["shadow_y_start"] = y_start

    return img, metadata


def generate_v2(img: np.ndarray) -> tuple[np.ndarray, dict]:
    """
    v2: 中度退化版
    目標：
    - 明顯比 v1 更難
    - 模擬一般掃描 / 拍照品質
    - OCR 開始有挑戰，但不應完全毀損

    處理內容：
    1. 中度降解析度
    2. 模糊
    3. 輕微旋轉
    4. 少量噪聲
    5. 明顯但仍合理的亮度不均
    """
    metadata = {}

    # 1. 中度降解析度
    scale = random.choice([0.55, 0.60, 0.65])
    img = apply_low_resolution(img, scale=scale)
    metadata["resolution_scale"] = scale

    # 2. 模糊
    blur_kernel = random.choice([3, 5])
    img = apply_blur(img, kernel_size=blur_kernel)
    metadata["blur_kernel"] = blur_kernel

    # 3. 小角度旋轉
    angle = random.choice([-4.0, -3.0, -2.0, 2.0, 3.0, 4.0])
    img = apply_rotation(img, angle=angle)
    metadata["rotation_angle"] = angle

    # 4. 雜訊
    sigma = random.choice([6.0, 8.0, 10.0])
    img = apply_noise(img, sigma=sigma)
    metadata["noise_sigma"] = sigma

    # 5. 陰影
    x_start = random.choice([0.84, 0.86, 0.88])
    y_start = random.choice([0.88, 0.90, 0.92])
    img = apply_shadow(img, x_start=x_start, y_start=y_start)
    metadata["shadow"] = True
    metadata["shadow_x_start"] = x_start
    metadata["shadow_y_start"] = y_start

    return img, metadata


# =========================
# Metadata 輸出
# =========================
def write_metadata(doc_id: str, v1_meta: dict, v2_meta: dict) -> None:
    """
    為每份文件輸出 metadata。
    這份 metadata 很重要，後面做 error analysis 會用到。
    """
    category = infer_category_from_doc_id(doc_id)

    metadata = {
        "source_id": doc_id,
        "category": category,
        "image_versions": [
            {
                "version": "clean",
                "visual_style": "rendered_clean",
                "blur_level": 0,
                "skew_level": 0,
                "resolution_level": "original",
                "noise_level": 0,
                "shadow_level": 0
            },
            {
                "version": "v1",
                "visual_style": "lightly_degraded",
                "blur_level": 1,
                "skew_level": 0,
                "resolution_level": "high",
                "noise_level": 0,
                "shadow_level": 1,
                "params": v1_meta
            },
            {
                "version": "v2",
                "visual_style": "scanned_degraded",
                "blur_level": 2,
                "skew_level": 1,
                "resolution_level": "medium",
                "noise_level": 1,
                "shadow_level": 1,
                "params": v2_meta
            }
        ]
    }

    out_path = META_DIR / f"{doc_id}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


# =========================
# 主流程
# =========================
def process_single_image(img_path: Path) -> None:
    """
    處理單一 clean PNG：
    - 生成 v1
    - 生成 v2
    - 寫 metadata
    """
    doc_id = img_path.stem
    img = load_image_cv(img_path)

    # v1：輕度退化
    v1_img, v1_meta = generate_v1(img)
    save_image_cv(V1_DIR / f"{doc_id}_v1.png", v1_img)

    # v2：中度退化
    v2_img, v2_meta = generate_v2(img)
    save_image_cv(V2_DIR / f"{doc_id}_v2.png", v2_img)

    # metadata
    write_metadata(doc_id, v1_meta, v2_meta)

    print(f"[OK] Generated v1/v2 + metadata for {doc_id}")


def main() -> None:
    """
    批次處理 clean PNG。
    先建議用 [:5] 或 [:10] 測試，確認滿意後再拿掉。
    """
    image_files = sorted(CLEAN_DIR.glob("*.png"))

    if not image_files:
        print("[WARN] No clean PNG files found.")
        return

    print(f"[INFO] Found {len(image_files)} clean PNG files.")

    for image_file in image_files:
        process_single_image(image_file)

    print(f"\nDone. Processed {len(image_files)} images.")


if __name__ == "__main__":
    main()