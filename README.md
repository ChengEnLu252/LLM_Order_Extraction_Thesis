# Applying Large Language Models for Key Information Extraction and Standardization in Heterogeneous Order Documents

本 repository 為本人碩士論文實驗專案，研究主題為：

**應用大型語言模型於異質訂單文件之關鍵資訊擷取與標準化研究**  
**Applying Large Language Models for Key Information Extraction and Standardization in Heterogeneous Order Documents**

本研究探討大型語言模型（LLM）在不同文件複雜度與不同輸入型態下，對訂單關鍵資訊擷取與標準化的表現，並由純文字文件逐步延伸至影像型文件。

---

## 研究目標

本研究的核心目標，是驗證大型語言模型是否能從異質訂單文件中，穩定擷取並標準化以下關鍵欄位：

- `po_number`
- `po_date`
- `currency`
- `total_amount`
- `items`
  - `part_number`
  - `quantity`
  - `unit`
  - `unit_price`
  - `line_amount`

---

## 統一 Schema

所有實驗層級皆使用相同 schema 作為輸出與評估基準：

```json
{
  "po_number": null,
  "po_date": null,
  "currency": null,
  "total_amount": null,
  "items": [
    {
      "part_number": null,
      "quantity": null,
      "unit": null,
      "unit_price": null,
      "line_amount": null
    }
  ]
}

標準化原則
	•	po_date 統一為 YYYY-MM-DD
	•	total_amount、unit_price、line_amount 皆輸出為純數值
	•	缺漏欄位以 null 表示
	•	items 為逐筆明細陣列，不可任意跨列拼接

⸻

研究架構

本研究分為三個實驗層級：

Level 1 — Simple Text Orders

簡單純文字訂單實驗
用於建立 baseline、驗證 schema 與整體抽取流程之基本可行性。

Level 2 — Complex Text Orders

複雜純文字訂單實驗
用於測試模型在高異質文字情境下的穩定性，並分析主要錯誤型態。

Level 3 — Image Documents

影像型訂單文件實驗
以 Level 2 內容為母體轉製為影像文件，並比較兩條處理路線：
	1.	OCR-based pipeline
image → OCR → LLM → JSON
	2.	Vision Direct pipeline
image → multimodal LLM → JSON

⸻

專案結構
.
├── Level1/
├── Level2/
├── Level3/
├── .gitignore
└── README.md

Level1

簡單純文字訂單實驗
	•	建立 baseline
	•	驗證 schema 與評估流程
	•	確認低複雜度條件下的抽取可行性

Level2

複雜純文字訂單實驗
	•	測試欄位名稱變異、資訊分散、複雜明細與干擾資訊
	•	比較 baseline 與 improved prompt
	•	分析代表性錯誤
	•	驗證日期標準化改善支線

Level3

影像型訂單文件實驗
	•	比較 OCR-based 與 Vision Direct
	•	分析 OCR 所引入的錯誤傳遞
	•	驗證 OCR 在結構化抽取任務中的必要性
	•	驗證 OCR 字元混淆修正支線

⸻

Level 2 類型設計

Level 2 共 250 份訂單，分為五類，每類 50 份：
	•	A — Field Variation
欄位名稱變異
	•	B — Scattered Fields
關鍵資訊分散於不同區塊
	•	C — Complex Items
明細表達不規則、跨行或半敘述式
	•	D — Noise Information
加入 subtotal、tax、shipping fee、聯絡資訊等干擾內容
	•	E — Mixed Complexity
綜合多種複雜因素

⸻

Level 3 正式納入版本

Level 3 正式實驗僅納入以下兩種影像版本：
	•	clean
	•	v1

註：其他影像版本曾作額外測試，但不納入正式論文分析。
Vision Direct 路線僅作比較用途，正式結論為目前條件下幾乎不可用。

⸻

Prompt 設計

各層級皆比較兩種 prompt：
	•	baseline
	•	較簡潔
	•	著重 schema、JSON 輸出與基本標準化規則
	•	improved
	•	較詳細
	•	額外加入更多格式限制、OCR 情境說明與判讀規則

本研究的重要觀察之一是：

Prompt 並非越複雜越好。
在多數實驗中，baseline 版本反而較穩定。

⸻

評估方式

各階段皆使用以下三類報表進行分析：
	1.	Document Accuracy
	•	單份文件所有欄位皆完全正確才算正確
	2.	Field Accuracy
	•	各欄位正確率
	3.	Error Report
	•	錯誤欄位、錯誤類型與案例整理

額外分析
	•	Level 2：category-level analysis
	•	Level 3：OCR-based vs Vision Direct 比較
	•	Level 2 日期歧義改善支線
	•	Level 3 OCR 字元混淆改善支線

⸻

正式實驗結果

Level 1
	•	Baseline：100.0%（50/50）
	•	Improved：98.0%（49/50）

正式採用：Baseline

Level 2
	•	Baseline：95.2%（238/250）
	•	Improved：93.6%（234/250）

Level 2 baseline 各類型結果：
	•	A = 98%
	•	B = 90%
	•	C = 98%
	•	D = 92%
	•	E = 98%

主要錯誤：
	•	全部集中於 po_date
	•	核心原因為 dd/mm/yyyy 與 mm/dd/yyyy 之日期格式歧義

正式採用：Baseline

Level 3 OCR-based

clean
	•	Baseline：86.8%（217/250）
	•	Improved：85.6%（214/250）

v1
	•	Baseline：82.8%（207/250）
	•	Improved：77.2%（193/250）

OCR-based 主要觀察：
	•	錯誤不再只集中於 po_date
	•	已擴展至：
	•	po_number
	•	part_number
	•	部分 item-level 欄位
	•	B 類（Scattered Fields）最脆弱

正式採用：clean baseline、v1 baseline

Level 3 Vision Direct

clean
	•	baseline_vision：1.2%（3/250）

v1
	•	baseline_vision：0.8%（2/250）

主要觀察：
	•	部分 header-level 欄位偶可辨識
	•	但整體 document-level 幾近不可用
	•	無法穩定完成多筆 item-level 結構化抽取

正式結論：Vision Direct 幾乎不可用，無法取代 OCR-based pipeline

⸻

支線實驗摘要

Level 2 日期標準化支線

針對 po_date 的格式歧義進行後處理實驗。

主要觀察：
	•	只靠文件內部日期線索，幾乎無法有效改善
	•	mm/dd/yyyy 預設策略雖僅小幅改善，但穩定性最佳
	•	修正策略不能只看「修正幾筆」，也要看是否造成誤修正

Level 3 OCR 字元混淆支線

針對 po_number 與 part_number 進行：
	•	uppercase normalization
	•	pattern-based correction

結果：
	•	clean：86.8% → 93.6%
	•	v1：82.8% → 93.2%

主要觀察：
	•	OCR error propagation 並非完全不可控
	•	對格式規律明確的欄位，可透過輕量級後處理獲得顯著改善

⸻

研究結論概要

1. 純文字訂單情境下，LLM 具高度可行性

Level 1 與 Level 2 結果顯示，大型語言模型在異質純文字訂單中已可穩定完成關鍵資訊擷取與標準化。

2. 純文字情境下的主要問題是標準化，而非欄位辨識

Level 2 的主要錯誤集中於 po_date，顯示模型多數情況下已能找到日期欄位，但在格式標準化決策時仍可能出錯。

3. 文件影像化後，OCR 會帶來額外誤差

Level 3 OCR-based 結果低於純文字情境，顯示 OCR 所造成的字元失真與結構破壞會影響後續抽取。

4. OCR-based pipeline 仍具實務價值

雖然表現下降，但 OCR-based 路線仍維持一定可用性，且可透過欄位導向後處理顯著改善。

5. Vision Direct 目前無法取代 OCR

在本研究任務中，直接將訂單影像輸入多模態 LLM 幾乎無法穩定完成完整 JSON 結構化輸出。

⸻

使用工具
	•	Python
	•	OpenAI API / gpt-4o-mini
	•	PaddleOCR
	•	OpenCV
	•	自製 evaluation scripts

⸻

作者

呂承恩
國立政治大學 應用數學研究所（AI / Data Science）

⸻

Notes

This repository contains the experimental implementation for the author’s master’s thesis.
The official thesis conclusions are based on:
	•	Level 1 baseline
	•	Level 2 baseline
	•	Level 3 OCR-based clean baseline
	•	Level 3 OCR-based v1 baseline

Vision Direct is included for comparison only and is not adopted as a practical solution under the current experimental setting.
