## Level 3 研究定位

Level 3 為本論文第三階段，目的在於評估大型語言模型在**影像型訂單文件**中的關鍵資訊擷取能力。

本階段延續 Level 2 的複雜訂單內容，但將文件形式由純文字擴展為影像，並進一步比較兩種方法路線：

1. **OCR-based pipeline**
2. **Vision Direct pipeline**

---

## 研究問題

Level 3 主要回答以下問題：

1. 當訂單由純文字轉為影像文件後，整體抽取表現會如何變化？
2. OCR 轉寫後再交由 LLM 抽取，是否仍具可用性？
3. 是否可以直接將圖片輸入多模態 LLM，而不經 OCR？
4. 在異質訂單文件情境下，OCR 是否仍然是必要步驟？

---

## 影像條件

本階段正式納入兩種影像版本：

- **clean**：高品質影像版本
- **v1**：輕度退化影像版本

---

## 兩條實驗路線

### 1. OCR-based pipeline
流程如下：

```text
image → resize → OCR → OCR text → LLM → JSON

此路線用來觀察：
	•	OCR 對抽取結果的影響
	•	OCR 所引入的字元級誤差
	•	影像退化是否會進一步放大錯誤

⸻

2. Vision Direct pipeline

流程如下：
image → multimodal LLM → JSON

此路線用來觀察：
	•	是否可直接將圖片輸入模型
	•	不經 OCR 是否仍能完成結構化抽取
	•	direct vision 與 OCR-based 的差異

⸻

抽取欄位（Schema）
	•	po_number
	•	po_date
	•	currency
	•	total_amount
	•	items
	•	part_number
	•	quantity
	•	unit
	•	unit_price
	•	line_amount

⸻

資料夾說明
Level3/
├── dataset/
├── scripts/
├── result/
├── reports/
├── schema.json
└── README.md

dataset

存放 Level 3 影像資料、OCR 輸出、metadata 與相關中間資料。

scripts

存放影像生成、OCR、vision direct、抽取、evaluation 等程式。

result

存放 OCR-based 與 vision direct 的 baseline / improved prediction 結果。

reports

存放各路線的 document accuracy、field accuracy、error report 與正式結果報告。

schema.json

存放本研究正式使用的抽取 schema。

⸻

Level 3 重點結論

OCR-based
	•	相較 Level 2 純文字結果，整體表現下降
	•	但仍具有實際可用性
	•	OCR 引入了新的字元級錯誤
	•	資訊分散型文件（B 類）最脆弱
	•	baseline prompt 仍是較穩定版本

Vision Direct
	•	直接將圖片輸入 LLM 的 document accuracy 極低
	•	header-level 欄位有部分可辨識能力
	•	item-level 抽取幾乎無法穩定完成
	•	improved_vision 未帶來實質改善

整體結論
	•	direct vision 無法穩定取代 OCR-based pipeline
	•	OCR 雖然耗時，但在此任務中具有重要價值
	•	對於異質訂單文件的結構化資訊擷取，OCR 目前仍是不可輕易省略的重要步驟
