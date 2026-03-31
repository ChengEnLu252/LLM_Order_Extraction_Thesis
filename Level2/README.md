## Level 2 研究定位

Level 2 為本論文第二階段，目的在於評估大型語言模型在**複雜純文字訂單文件**中的資訊擷取能力。

相較於 Level 1 的簡單場景，Level 2 特別提高資料異質性與文件複雜度，讓模型面對更接近真實商業文件的文字情境。

---

## Level 2 複雜性設計

本階段資料共分為五類，每類各 50 筆：

- **A 類：Field Variation**  
  欄位名稱變異

- **B 類：Scattered Fields**  
  關鍵資訊分散於不同段落或區塊

- **C 類：Complex Items**  
  明細格式不規則、跨行或混合表達

- **D 類：Noise Information**  
  含大量干擾資訊，例如 subtotal、tax、shipping 等

- **E 類：Mixed Complexity**  
  多種複雜因素同時存在

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

Level 2 延續 Level 1 的兩組 prompt：

1. **baseline prompt**
2. **improved prompt**

本階段重點在於分析：

- 複雜文字條件下的整體抽取穩定性
- 各類型複雜性對結果的影響
- improved prompt 是否能改善 Level 2 的錯誤來源

---

## 資料夾說明

```text
Level2/
├── dataset/
├── scripts/
├── result/
├── reports/
└── README.md

dataset

存放複雜純文字訂單資料、ground truth 與相關 metadata。

scripts

存放資料生成、抽取、評估與分析程式。

result

存放 baseline / improved 的 prediction JSON。

reports

存放 document accuracy、field accuracy、error report 以及正式結果報告。

⸻

Level 2 重點結論
	•	模型在複雜純文字訂單中仍維持高準確率
	•	主要錯誤集中在 po_date
	•	dd/mm/yyyy 與 mm/dd/yyyy 的格式歧義是主要錯誤來源
	•	item-level 欄位在本階段表現非常穩定
	•	improved prompt 未帶來整體提升，baseline 仍是較穩定的正式採用版本
