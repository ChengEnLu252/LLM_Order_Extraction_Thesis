## Level 1 研究定位

Level 1 為本論文的第一階段，目的在於先驗證大型語言模型是否能從**簡單、結構明確的純文字訂單文件**中，穩定抽取出預先定義的關鍵欄位資訊。

本階段的重點不是追求高複雜度場景下的表現，而是建立：

- 可用的 schema
- 可行的 extraction pipeline
- 可驗證的 evaluation 流程
- 後續 Level 2 與 Level 3 可比較的 baseline

---

## 資料特性

Level 1 使用 Python 自行生成的純文字訂單資料。

特徵如下：

- 文件格式單純
- 欄位名稱固定
- 整體結構清楚
- 幾乎不含異質性干擾

每份訂單皆對應一份 ground truth JSON，作為正式評估標準。

---

## 抽取欄位（Schema）

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
- 較簡潔 prompt 與較高約束 prompt
- 是否會對抽取結果造成差異

---

## 資料夾說明

```text
Level1/
├── dataset/
├── scripts/
├── result/
├── reports/
└── README.md

dataset

存放 Level 1 訂單資料與 ground truth。

scripts

存放資料生成、抽取、評估等程式。

result

存放模型抽取輸出結果。

reports

存放 document accuracy、field accuracy、error report 與結果報告。

⸻

Level 1 重點結論
	•	baseline prompt 在本階段表現最穩定
	•	improved prompt 未帶來提升，反而在個別欄位出現漏抽
	•	Level 1 成功驗證了整體抽取流程的可行性
	•	本階段建立的 baseline 成為後續 Level 2、Level 3 的比較基礎
