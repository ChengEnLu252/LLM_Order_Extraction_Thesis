# Applying Large Language Models for Key Information Extraction and Standardization in Heterogeneous Order Documents

本 repository 為本人碩士論文實驗專案，主題為：

**應用大型語言模型於異質訂單文件之關鍵資訊擷取與標準化研究**

本研究探討大型語言模型（LLM）在不同文件難度與不同輸入形式下，對訂單關鍵資訊抽取與標準化的表現，並逐步從純文字文件延伸至影像型文件。

---

## 研究目標

本論文的核心目標，是驗證大型語言模型是否能從異質訂單文件中，穩定抽取並標準化以下關鍵欄位：

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

## 專案結構

```text
.
├── Level1/
├── Level2/
├── Level3/
├── .gitignore
└── README.md

Level1

簡單純文字訂單實驗。
用於建立 baseline、驗證 schema 與整體抽取流程是否可行。

Level2

複雜純文字訂單實驗。
用於測試模型在欄位名稱變異、資訊分散、複雜明細與干擾資訊情境下的穩定性。

Level3

影像型訂單實驗。
包含兩條研究路線：
	1.	OCR-based pipeline
image → OCR → LLM → JSON
	2.	Vision Direct pipeline
image → multimodal LLM → JSON

本階段進一步比較：
	•	純文字 vs 影像文件
	•	OCR-based vs direct vision
	•	baseline prompt vs improved prompt

⸻
各層級研究重點

Level 1
	•	簡單、結構明確的純文字訂單
	•	驗證 schema 與評估方式
	•	建立正式 baseline

Level 2
	•	複雜純文字訂單
	•	分析不同類型複雜性對抽取表現的影響
	•	比較 baseline 與 improved prompt

Level 3
	•	影像型訂單文件
	•	比較 OCR-based 與 direct vision 兩種方法
	•	分析 OCR 所引入的誤差類型
	•	驗證 OCR 在結構化抽取任務中的必要性

⸻

評估方式

各階段皆使用以下三類報表進行分析：
	1.	document-level accuracy
	2.	field-level accuracy
	3.	error report

Level 2 與 Level 3 另外納入 category-level 分析，以觀察不同類型文件的表現差異。

⸻

研究結論概要

Level 1

在簡單純文字訂單中，LLM 可穩定完成資訊抽取，baseline prompt 已足以支撐任務需求。

Level 2

在複雜純文字訂單中，模型仍維持高準確率，主要錯誤集中於 po_date 的日期格式歧義。

Level 3

當訂單文件轉為影像後：
	•	OCR-based pipeline 仍具可用性，但表現較純文字下降
	•	Vision Direct pipeline 在此任務中無法穩定取代 OCR
	•	結果顯示：OCR 雖然耗時，但在異質訂單文件的結構化抽取任務中仍具有重要價值

⸻

使用工具
	•	Python
	•	OpenAI API / gpt-4o-mini
	•	PaddleOCR
	•	OpenCV
	•	自製 evaluation scripts

作者

呂承恩
國立政治大學 應用數學研究所（AI / Data Science）
