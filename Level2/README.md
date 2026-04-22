# Level 2 — Complex Text Orders

## Level 2 研究定位

Level 2 為本研究的第二個實驗層級，目的在於評估大型語言模型在**複雜純文字訂單文件**中的資訊擷取能力。

相較於 Level 1 的簡單場景，Level 2 明顯提高資料異質性與文件複雜度，使模型面對更接近真實商務文件的純文字情境。  
本階段的重點不只是觀察整體準確率是否下降，更重要的是分析：

- 在高異質純文字條件下，模型是否仍能穩定抽取關鍵欄位
- 不同複雜性類型會對結果造成何種影響
- 主要錯誤究竟來自欄位辨識，還是來自標準化決策
- improved prompt 是否能有效改善代表性錯誤

換言之，Level 2 是整篇研究中最關鍵的純文字實驗層級，用來觀察 LLM 在高異質文字文件中的穩定性與能力邊界。

---

## Level 2 複雜性設計

本階段資料共 250 份，分為五類，每類各 50 份：

- **A 類：Field Variation**  
  欄位名稱變異

- **B 類：Scattered Fields**  
  關鍵資訊分散於不同段落或區塊

- **C 類：Complex Items**  
  明細格式不規則、跨行或混合表達

- **D 類：Noise Information**  
  含大量干擾資訊，例如 subtotal、tax、shipping、聯絡資訊等

- **E 類：Mixed Complexity**  
  多種複雜因素同時存在

此一設計使不同複雜因素得以被相對獨立地觀察，也能進一步分析哪一種類型對模型最具挑戰性。

---

## 抽取欄位（Schema）

Level 2 與其他層級共用相同 schema，包含以下欄位：

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
- 主要錯誤來源是否集中於特定欄位
- improved prompt 是否能改善代表性錯誤

此外，根據 Level 2 主實驗結果，本階段亦延伸出 **日期標準化支線實驗**，進一步分析 `po_date` 的格式歧義問題。

---

## 資料夾結構

```text
Level2/
├── dataset/
├── scripts/
├── result/
├── reports/
└── README.md

dataset/

存放複雜純文字訂單資料、ground truth 與相關 metadata。

scripts/

存放資料生成、模型抽取、結果評估與錯誤分析程式。

result/

存放 baseline / improved 的 prediction JSON。

reports/

存放各類評估報表與正式分析結果，例如：
	•	document accuracy
	•	field accuracy
	•	error report
	•	category-level analysis
	•	正式結果摘要

⸻

正式實驗結果

Level 2 共使用 250 份複雜純文字訂單進行測試，結果如下：
	•	baseline：95.2%（238/250）
	•	improved：93.6%（234/250）

正式採用版本為：
	•	baseline

baseline 各類型結果
	•	A = 98%
	•	B = 90%
	•	C = 98%
	•	D = 92%
	•	E = 98%

⸻

Level 2 代表性發現

1. 模型在複雜純文字訂單中仍維持高準確率

即使面對欄位名稱變異、資訊分散、複雜明細與干擾資訊增加等高異質情境，baseline 仍達 95.2%，顯示 LLM 在複雜純文字文件中具備相當高的可用性。

2. 主要錯誤集中於 po_date

Level 2 的代表性錯誤幾乎全部集中於 po_date，顯示問題並非整體欄位崩解，而是集中於特定格式敏感欄位。

3. 日期格式歧義是核心問題

dd/mm/yyyy 與 mm/dd/yyyy 的月日順序歧義，是本階段最主要的錯誤來源。
也就是說，模型多數情況下已能辨識日期欄位，但在最終標準化時仍可能做出錯誤決策。

4. item-level 欄位表現非常穩定

在本階段中，item-level 欄位整體表現極穩定，顯示即使在複雜明細表達條件下，模型仍具相當不錯的結構整理能力。

5. improved prompt 未帶來整體提升

雖然 improved prompt 加入更多規則與約束，但並未提升整體表現，反而使 document accuracy 由 95.2% 降為 93.6%。
因此，Level 2 正式採用 baseline 作為代表結果。

⸻

日期標準化支線實驗

由於 Level 2 的主要錯誤集中於 po_date，本階段另行設計日期標準化支線，以驗證不同後處理策略是否能改善歧義日期錯誤。

主要觀察如下：
	•	只依賴文件內部日期線索，幾乎無法有效改善結果
	•	固定 dd/mm/yyyy 雖能修正較多原始錯誤，但會造成明顯過度修正
	•	固定 mm/dd/yyyy 雖僅帶來小幅改善，但穩定性最佳

這顯示：

對於格式敏感欄位而言，修正策略不能只看修正了多少錯誤，也必須同時考量是否破壞原本正確案例。

⸻

Level 2 重點結論
	•	模型在複雜純文字訂單中仍維持高準確率
	•	主要錯誤集中在 po_date
	•	dd/mm/yyyy 與 mm/dd/yyyy 的格式歧義是核心錯誤來源
	•	item-level 欄位在本階段表現非常穩定
	•	improved prompt 未帶來整體提升，baseline 仍是較穩定的正式採用版本
	•	Level 2 顯示：在高異質純文字情境下，模型的主要限制不一定是欄位辨識，而可能是標準化決策

⸻

Summary

Level 2 shows that LLM-based extraction remains highly effective in complex text-based order documents.
The major limitation is not general field recognition failure, but date standardization ambiguity, especially in the po_date field.
Baseline remains the officially adopted version at this level.
