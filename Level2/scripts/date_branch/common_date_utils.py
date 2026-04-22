from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# =========================
# 路徑工具
# =========================
def get_level2_root() -> Path:
    """
    取得 Level2 根目錄。
    假設本檔案位置為：
    Level2/scripts/date_branch/common_date_utils.py
    """
    return Path(__file__).resolve().parents[2]


def ensure_dir(path: Path) -> None:
    """若資料夾不存在則建立。"""
    path.mkdir(parents=True, exist_ok=True)


# =========================
# 檔案工具
# =========================
def load_json(path: Path) -> dict:
    """讀取 JSON 檔。"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: dict, path: Path) -> None:
    """儲存 JSON 檔。"""
    ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def read_text(path: Path) -> str:
    """讀取文字檔。"""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def get_stem_to_file_map(folder: Path, suffixes: Tuple[str, ...]) -> Dict[str, Path]:
    """
    遞迴建立 stem -> file_path 映射。
    
    支援像這種結構：
    order_level2/
        A_field_variation/
            L2_A_001.txt
        B_scattered_fields/
            L2_B_001.txt

    例如：
    L2_A_001.txt -> {"L2_A_001": Path(...)}
    """
    mapping: Dict[str, Path] = {}

    # rglob("*") 會遞迴搜尋所有子資料夾與檔案
    for file_path in folder.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in suffixes:
            stem = file_path.stem

            # 若不同資料夾下出現重複 stem，直接報錯，避免覆蓋
            if stem in mapping:
                raise ValueError(
                    f"Duplicate file stem detected: {stem}\n"
                    f"Existing: {mapping[stem]}\n"
                    f"New: {file_path}"
                )

            mapping[stem] = file_path

    return mapping


# =========================
# 日期處理
# =========================
DATE_PATTERNS = [
    r"\b\d{1,2}/\d{1,2}/\d{4}\b",   # 03/04/2025
    r"\b\d{1,2}-\d{1,2}-\d{4}\b",   # 03-04-2025
    r"\b\d{4}/\d{1,2}/\d{1,2}\b",   # 2025/03/04
    r"\b\d{4}-\d{1,2}-\d{1,2}\b",   # 2025-03-04
]

DATE_REGEXES = [re.compile(p) for p in DATE_PATTERNS]

DATE_KEYWORDS = [
    "order date",
    "po date",
    "purchase date",
    "issue date",
    "date",
    "ordered on",
    "order placed",
    "document date",
]


@dataclass
class DateMatch:
    raw_date: str
    start: int
    end: int
    keyword: Optional[str]
    distance_to_keyword: int
    line_text: str


def normalize_spaces(text: str) -> str:
    """將多重空白簡單壓縮，方便規則判斷。"""
    return re.sub(r"[ \t]+", " ", text)


def find_all_date_matches(text: str) -> List[DateMatch]:
    """
    找出文件中所有日期字串，並計算其與日期關鍵字的距離。
    後續會優先選擇最像 po_date 的那個日期。
    """
    text_lower = text.lower()
    lines = text.splitlines()
    line_boundaries = []
    current = 0
    for line in lines:
        start = current
        end = current + len(line)
        line_boundaries.append((start, end, line))
        current = end + 1  # 換行符

    keyword_positions: List[Tuple[str, int]] = []
    for kw in DATE_KEYWORDS:
        for m in re.finditer(re.escape(kw), text_lower):
            keyword_positions.append((kw, m.start()))

    matches: List[DateMatch] = []
    for regex in DATE_REGEXES:
        for m in regex.finditer(text):
            date_str = m.group(0)
            start, end = m.start(), m.end()

            # 找該日期所在行
            line_text = ""
            for ls, le, line in line_boundaries:
                if ls <= start <= le:
                    line_text = line
                    break

            # 找最近 keyword
            best_keyword = None
            best_dist = 10**9
            for kw, kw_pos in keyword_positions:
                dist = abs(start - kw_pos)
                if dist < best_dist:
                    best_dist = dist
                    best_keyword = kw

            if best_keyword is None:
                best_dist = 10**9

            matches.append(
                DateMatch(
                    raw_date=date_str,
                    start=start,
                    end=end,
                    keyword=best_keyword,
                    distance_to_keyword=best_dist,
                    line_text=line_text.strip(),
                )
            )

    return matches


def choose_primary_po_date_candidate(text: str) -> Optional[DateMatch]:
    """
    從所有日期中挑選最像 po_date 的日期：
    1. 優先同一行含 date keyword
    2. 再看與 keyword 距離
    3. 若仍無法區分，取最前面的日期
    """
    matches = find_all_date_matches(text)
    if not matches:
        return None

    def score(m: DateMatch) -> Tuple[int, int, int]:
        line_lower = m.line_text.lower()
        has_keyword_in_line = any(kw in line_lower for kw in DATE_KEYWORDS)
        keyword_penalty = 0 if has_keyword_in_line else 1
        return (keyword_penalty, m.distance_to_keyword, m.start)

    matches.sort(key=score)
    return matches[0]


def parse_date_string(raw_date: str) -> Optional[dict]:
    """
    解析日期字串，支援：
    - dd/mm/yyyy
    - mm/dd/yyyy
    - dd-mm-yyyy
    - mm-dd-yyyy
    - yyyy/mm/dd
    - yyyy-mm-dd

    回傳格式：
    {
        "raw": "03/04/2025",
        "format_type": "ambiguous_slash" / "ambiguous_dash" / "ymd",
        "parts": (a, b, yyyy),
        "is_ambiguous": True/False,
        "candidate_mmdd": "2025-03-04" or None,
        "candidate_ddmm": "2025-04-03" or None,
        "direct_normalized": "2025-03-04" or None,
    }
    """
    raw_date = raw_date.strip()

    # yyyy/mm/dd or yyyy-mm-dd
    m = re.fullmatch(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", raw_date)
    if m:
        year = int(m.group(1))
        month = int(m.group(2))
        day = int(m.group(3))
        if is_valid_ymd(year, month, day):
            return {
                "raw": raw_date,
                "format_type": "ymd",
                "parts": (year, month, day),
                "is_ambiguous": False,
                "candidate_mmdd": None,
                "candidate_ddmm": None,
                "direct_normalized": f"{year:04d}-{month:02d}-{day:02d}",
            }
        return None

    # dd/mm/yyyy or mm/dd/yyyy or dash version
    m = re.fullmatch(r"(\d{1,2})([/-])(\d{1,2})\2(\d{4})", raw_date)
    if m:
        a = int(m.group(1))
        sep = m.group(2)
        b = int(m.group(3))
        year = int(m.group(4))

        candidate_mmdd = None
        candidate_ddmm = None

        if is_valid_ymd(year, a, b):
            candidate_mmdd = f"{year:04d}-{a:02d}-{b:02d}"
        if is_valid_ymd(year, b, a):
            candidate_ddmm = f"{year:04d}-{b:02d}-{a:02d}"

        is_ambiguous = (
            a <= 12 and b <= 12 and candidate_mmdd is not None and candidate_ddmm is not None
        )

        direct_normalized = None
        if not is_ambiguous:
            # 若其中一個 > 12，則可直接判斷
            if a > 12 and candidate_ddmm is not None:
                direct_normalized = candidate_ddmm
            elif b > 12 and candidate_mmdd is not None:
                direct_normalized = candidate_mmdd

        return {
            "raw": raw_date,
            "format_type": "ambiguous_slash" if sep == "/" else "ambiguous_dash",
            "parts": (a, b, year),
            "is_ambiguous": is_ambiguous,
            "candidate_mmdd": candidate_mmdd,
            "candidate_ddmm": candidate_ddmm,
            "direct_normalized": direct_normalized,
        }

    return None


def is_valid_ymd(year: int, month: int, day: int) -> bool:
    """檢查基本日期合法性，不用額外第三方套件。"""
    if month < 1 or month > 12:
        return False
    if day < 1:
        return False

    days_in_month = [31, 29 if is_leap_year(year) else 28, 31, 30, 31, 30,
                     31, 31, 30, 31, 30, 31]
    return day <= days_in_month[month - 1]


def is_leap_year(year: int) -> bool:
    """判斷閏年。"""
    return year % 400 == 0 or (year % 4 == 0 and year % 100 != 0)


def extract_unambiguous_date_formats(text: str) -> List[str]:
    """
    從文件中找出可直接判斷格式方向的日期，回傳格式方向清單：
    - "mmdd"
    - "ddmm"
    - "ymd"

    例如：
    - 18/04/2025 -> ddmm
    - 04/18/2025 -> mmdd
    - 2025-04-18 -> ymd
    """
    results: List[str] = []
    matches = find_all_date_matches(text)
    for match in matches:
        parsed = parse_date_string(match.raw_date)
        if not parsed:
            continue

        if parsed["format_type"] == "ymd":
            results.append("ymd")
            continue

        if parsed["is_ambiguous"]:
            continue

        a, b, _ = parsed["parts"]
        if a > 12:
            results.append("ddmm")
        elif b > 12:
            results.append("mmdd")

    return results


def infer_format_hint_from_text(text: str) -> Optional[str]:
    """
    根據文件其他明確日期推測格式：
    - 若文件中有明顯 dd/mm/yyyy -> 回傳 "ddmm"
    - 若文件中有明顯 mm/dd/yyyy -> 回傳 "mmdd"
    - 否則回傳 None
    """
    formats = extract_unambiguous_date_formats(text)
    ddmm_count = formats.count("ddmm")
    mmdd_count = formats.count("mmdd")

    if ddmm_count > 0 and ddmm_count > mmdd_count:
        return "ddmm"
    if mmdd_count > 0 and mmdd_count > ddmm_count:
        return "mmdd"
    return None


def detect_day_month_swap(pred: str, gt: str) -> bool:
    """
    檢查 pred 與 gt 是否屬於同一年但月日對調。
    例如：
    pred = 2025-04-03
    gt   = 2025-03-04
    """
    try:
        py, pm, pd = pred.split("-")
        gy, gm, gd = gt.split("-")
    except Exception:
        return False

    return py == gy and pm == gd and pd == gm


def safe_get_po_date(obj: dict) -> Optional[str]:
    """安全讀取 po_date。"""
    value = obj.get("po_date")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None