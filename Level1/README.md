# Level 1 — Simple Text Orders

## Level 1 研究定位

Level 1 為本研究的第一個實驗層級，目的在於先驗證大型語言模型是否能從**簡單、結構明確的純文字訂單文件**中，穩定抽取出預先定義的關鍵欄位資訊。

本階段的重點並不是追求高複雜度場景下的極限表現，而是建立整體研究的基礎，包括：

- 可用的 schema
- 可行的 extraction pipeline
- 可驗證的 evaluation 流程
- 可作為後續 Level 2 與 Level 3 比較基準的 baseline

換言之，Level 1 的角色是先確認：在低複雜度、低干擾的純文字條件下，整體資料生成、模型抽取、JSON 輸出與評估流程是否能穩定運作。

---

## 資料特性

Level 1 使用 Python 自行生成的純文字訂單資料，每份訂單皆同步建立對應的 ground truth JSON，作為正式評估標準。

本層級資料具有以下特徵：

- 文件格式單純
- 欄位名稱固定
- 整體結構清楚
- 幾乎不含異質性干擾
- 適合作為基礎可行性驗證資料

---

## 抽取欄位（Schema）

Level 1 與其他層級共用相同 schema，包含以下欄位：

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

## 實驗內容

本階段主要比較兩組 prompt：

1. **baseline prompt**
2. **improved prompt**

比較目的在於觀察：

- 在簡單純文字訂單場景下
- 較簡潔的 prompt
- 與較高約束、較詳細規則的 prompt
- 是否會對抽取結果造成差異

本研究的重要觀察之一是：  
即使在簡單情境下，prompt 並非越複雜越好；增加額外規則不一定能帶來更穩定的結果。

---

## 資料夾結構

```text
Level1/
├── dataset/
├── scripts/
├── result/
├── reports/
└── README.md

dataset/

存放 Level 1 純文字訂單資料與對應的 ground truth。

scripts/

存放資料生成、模型抽取、結果評估等實驗程式。

result/

存放模型抽取輸出的 JSON 結果。

reports/

存放各類評估報表與結果分析，例如：
	•	document accuracy
	•	field accuracy
	•	error report
	•	結果摘要報告

⸻

正式實驗結果

Level 1 共使用 50 份簡單純文字訂單進行測試，結果如下：
	•	baseline：100.0%（50/50）
	•	improved：98.0%（49/50）

正式採用版本為：
	•	baseline

⸻

Level 1 重點結論
	•	baseline prompt 在本階段表現最穩定
	•	improved prompt 未帶來提升，反而在個別欄位出現漏抽
	•	Level 1 成功驗證了整體抽取流程的可行性
	•	schema、資料生成、模型抽取與評估流程皆可穩定運作
	•	本階段建立的 baseline 成為後續 Level 2 與 Level 3 的比較基礎

⸻

Summary

Level 1 confirms that LLM-based extraction is highly feasible for simple text-based order documents.
It serves as the foundation of the full thesis pipeline and provides the baseline for subsequent comparisons in Level 2 and Level 3.
