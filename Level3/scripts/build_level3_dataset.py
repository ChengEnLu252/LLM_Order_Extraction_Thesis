from pathlib import Path
import subprocess
import sys


BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPT_DIR = BASE_DIR / "scripts"


def run_script(script_name: str) -> None:
    """
    執行單一腳本，若失敗則直接停止。
    """
    script_path = SCRIPT_DIR / script_name

    print(f"\n[RUN] {script_name}")
    result = subprocess.run([sys.executable, str(script_path)])

    if result.returncode != 0:
        raise RuntimeError(f"Script failed: {script_name}")


def main() -> None:
    """
    Level 3 dataset 建立總流程：
    1. txt -> HTML
    2. HTML -> clean PNG
    3. clean PNG -> v1/v2 + metadata
    """
    run_script("build_html.py")
    run_script("render_png.py")
    run_script("degrade_images.py")

    print("\n[OK] Level 3 dataset build completed successfully.")


if __name__ == "__main__":
    main()