# Level 3 — Image Documents

## Level 3 研究定位

Level 3 為本研究的第三個實驗層級，目的在於評估大型語言模型在**影像型訂單文件**中的關鍵資訊擷取能力。

本階段延續 Level 2 的複雜訂單內容，但將文件形式由純文字擴展為影像，並進一步比較兩種方法路線：

1. **OCR-based pipeline**
2. **Vision Direct pipeline**

Level 3 的研究重點不只是觀察影像條件下的整體準確率是否下降，而是進一步回答：

- 當訂單由純文字轉為影像後，整體表現會如何變化
- OCR 轉寫後再交由 LLM 抽取，是否仍具可用性
- 是否可以直接將影像輸入多模態 LLM 而不經 OCR
- 在異質訂單文件情境下，OCR 是否仍為必要步驟
- OCR 所引入的代表性錯誤，是否能透過後處理進一步改善

換言之，Level 3 是整篇研究中用來界定**影像文件處理能力邊界**的關鍵層級。

---

## 影像條件

Level 3 正式實驗僅納入兩種影像版本：

- **clean**：高品質影像版本
- **v1**：輕度退化影像版本

> 註：其他影像版本曾作額外測試，但**不納入正式論文分析與正式結果**。

---

## 研究問題

Level 3 主要回答以下問題：

1. 當訂單由純文字轉為影像文件後，整體抽取表現會如何變化？
2. OCR 轉寫後再交由 LLM 抽取，是否仍具可用性？
3. 是否可以直接將圖片輸入多模態 LLM，而不經 OCR？
4. 在異質訂單文件情境下，OCR 是否仍然是必要步驟？

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
	•	OCR-based pipeline 在影像訂單任務中的實際可用性

2. Vision Direct pipeline

流程如下：
image → multimodal LLM → JSON

此路線用來觀察：
	•	是否可直接將圖片輸入模型
	•	不經 OCR 是否仍能完成結構化抽取
	•	direct vision 與 OCR-based 的差異
	•	多模態模型是否具備穩定的 item-level 結構化能力

⸻

抽取欄位（Schema）

Level 3 與其他層級共用相同 schema，包含以下欄位：
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

實驗內容

Level 3 延續前兩層級的 prompt 設計，分別比較：
	•	baseline
	•	improved

其中：
	•	OCR-based 路線比較 baseline 與 improved
	•	Vision Direct 路線比較 baseline_vision 與 improved_vision

此外，根據 OCR-based 主實驗結果，Level 3 亦額外設計：
	•	OCR 字元混淆修正支線實驗

用來分析 po_number 與 part_number 等格式規律較強的欄位，是否可透過輕量級後處理顯著改善結果。

⸻

資料夾結構
Level3/
├── dataset/
├── scripts/
├── result/
├── reports/
├── schema.json
└── README.md

dataset/

存放 Level 3 影像資料、OCR 輸出、metadata 與相關中間資料。

scripts/

存放影像生成、OCR、Vision Direct、模型抽取、evaluation 與分析程式。

result/

存放 OCR-based 與 Vision Direct 的 baseline / improved prediction 結果。

reports/

存放各路線的 document accuracy、field accuracy、error report 與正式結果報告。

schema.json

存放本研究正式使用的抽取 schema。

⸻

正式實驗結果

OCR-based

clean
	•	baseline：86.8%（217/250）
	•	improved：85.6%（214/250）

v1
	•	baseline：82.8%（207/250）
	•	improved：77.2%（193/250）

正式採用版本：
	•	clean baseline
	•	v1 baseline

Vision Direct

clean
	•	baseline_vision：1.2%（3/250）

v1
	•	baseline_vision：0.8%（2/250）

正式結論：
	•	Vision Direct 僅作比較
	•	在本研究設定下幾乎不可用

⸻

OCR-based 代表性觀察
	•	相較於 Level 2 純文字結果，整體表現明顯下降
	•	但 OCR-based pipeline 仍具有實際可用性
	•	錯誤不再只集中於 po_date
	•	已擴展至：
	•	po_number
	•	part_number
	•	部分 item-level 欄位
	•	資訊分散型文件（B 類）最脆弱
	•	baseline prompt 仍是較穩定版本

B 類特別脆弱的原因

B 類（Scattered Fields）本來就需要模型跨區塊整合資訊。
當影像再經過 OCR 後，若文字出現破碎、欄位黏連或區塊邊界弱化，模型更難穩定還原完整欄位，因此在 clean 與 v1 條件下都成為最脆弱類型。

⸻

OCR 字元混淆支線結果

針對 po_number 與 part_number，本研究加入：
	•	uppercase normalization
	•	pattern-based correction

結果如下：

clean
	•	baseline：86.8% → 93.6%

v1
	•	baseline：82.8% → 93.2%

主要觀察：
	•	po_number 在 clean 與 v1 條件下皆提升至 100.0%
	•	未觀察到明顯誤修正
	•	顯示 OCR error propagation 並非完全不可控
	•	對格式規律明確的欄位，欄位導向之輕量級後處理可帶來顯著改善

⸻

Vision Direct 代表性觀察
	•	直接將圖片輸入 LLM 的 document accuracy 極低
	•	header-level 欄位有部分可辨識能力
	•	item-level 抽取幾乎無法穩定完成
	•	improved_vision 未帶來實質改善

關鍵解讀

Vision Direct 並不是完全「看不到內容」，而是常出現：
	•	局部欄位可辨識
	•	但整體 JSON 結構無法穩定維持
	•	多筆 item-level 明細無法正確對齊
	•	document-level 幾近不可用

也就是說，問題不只是辨識率，而是高結構要求任務下的整體輸出能力不足。

⸻

Level 3 重點結論

OCR-based
	•	相較 Level 2 純文字結果，整體表現下降
	•	但仍具有實際可用性
	•	OCR 引入了新的字元級錯誤與結構弱化問題
	•	資訊分散型文件（B 類）最脆弱
	•	baseline prompt 仍是較穩定版本
	•	欄位導向後處理可進一步顯著改善結果

Vision Direct
	•	直接將圖片輸入 LLM 的 document accuracy 極低
	•	header-level 欄位有部分可辨識能力
	•	item-level 抽取幾乎無法穩定完成
	•	improved_vision 未帶來實質改善
	•	目前無法作為 OCR-based pipeline 的替代方案

整體結論
	•	direct vision 無法穩定取代 OCR-based pipeline
	•	OCR 雖然耗時，但在此任務中具有重要價值
	•	對於異質訂單文件的結構化資訊擷取，OCR 目前仍是不可輕易省略的重要步驟

⸻

Summary

Level 3 evaluates LLM-based extraction on image-based order documents through two routes: OCR-based and Vision Direct.
The results show that OCR-based extraction remains usable, although performance drops compared with text-based settings.
By contrast, Vision Direct performs extremely poorly and cannot reliably replace OCR in this task.
This level confirms that OCR is still a critical intermediate step for structured extraction from heterogeneous order document images.
