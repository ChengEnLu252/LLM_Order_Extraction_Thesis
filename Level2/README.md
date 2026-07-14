# Level 2 — Complex Text Orders

## 研究定位

Level 2 為本研究的第二個實驗層級，目的在於評估大型語言模型在**複雜純文字訂單文件**中的資訊擷取能力。

相較於 Level 1 的簡單場景，Level 2 明顯提高資料異質性與文件複雜度，使模型面對更接近真實商務文件的純文字情境。本階段重點不只是觀察整體準確率是否下降，更要分析：

- 高異質純文字條件下，模型是否仍能穩定抽取關鍵欄位
- 不同複雜性類型對結果的影響
- 主要錯誤來自**欄位辨識**，還是**標準化決策**
- `improved` prompt 是否能有效改善代表性錯誤

Level 2 是整篇研究中最關鍵的純文字實驗層級，用來觀察 LLM 在高異質文字文件中的穩定性與能力邊界。

---

## 複雜性設計

本階段資料共 **250 份**，分為五類、每類各 50 份。五類各自對應一族**保語意擾動**（內容語意不變、只改變表面形式），用以逐類拆解模型弱點：

| 類別 | 名稱 | 複雜度來源 |
| --- | --- | --- |
| **A** | Field Variation | 欄位名稱變異、語序改變（`Order No.` vs `PO#`） |
| **B** | Scattered Fields | 關鍵資訊分散於不同段落／區塊，需跨段整合 |
| **C** | Complex Items | 明細跨行、合併儲存格、半敘述式列法 |
| **D** | Noise Information | 加入 subtotal、tax、shipping、條款、聯絡資訊等干擾 |
| **E** | Mixed Complexity | 多種複雜因素同時存在 |

---

## 抽取欄位（Schema）

Level 2 與其他層級共用相同 schema：

```json
{
  "po_number": null,
  "po_date": null,
  "currency": null,
  "total_amount": null,
  "items": [
    { "part_number": null, "quantity": null, "unit": null, "unit_price": null, "line_amount": null }
  ]
}
```

---

## 實驗內容

延續 Level 1 的兩組 prompt（`baseline` / `improved`），分析複雜文字條件下的整體穩定性、各類型複雜性影響、主要錯誤來源，以及 improved prompt 能否改善代表性錯誤。此外，依主實驗結果延伸出 **日期標準化支線實驗**，進一步分析 `po_date` 的格式歧義。

---

## 資料夾結構

```text
Level2/
├── dataset/   # 複雜純文字訂單資料、ground truth 與 metadata
├── scripts/   # 資料生成、模型抽取、評估與錯誤分析程式
├── result/    # baseline / improved 的 prediction JSON
├── reports/   # document / field accuracy、error report、category 分析、摘要
└── README.md
```

---

## 正式實驗結果

Level 2 共使用 **250 份**複雜純文字訂單：

| Prompt | Document Accuracy |
| --- | --- |
| **Baseline（正式採用）** | 95.2%（238/250） |
| Improved | 93.6%（234/250） |

**Baseline 各類型 Document Accuracy：**

| A | B | C | D | E |
| --- | --- | --- | --- | --- |
| 98% | 90% | 98% | 92% | 98% |

---

## 代表性發現

1. **模型在複雜純文字訂單中仍維持高準確率**——即使面對欄位變異、資訊分散、複雜明細與干擾資訊，baseline 仍達 95.2%。
2. **主要錯誤集中於 `po_date`**——其餘欄位皆 100%，並非整體欄位崩解，而是集中於特定格式敏感欄位。
3. **日期格式歧義是核心問題**——`dd/mm/yyyy` 與 `mm/dd/yyyy` 的月日順序歧義是最主要錯誤來源。模型多數情況已能辨識日期欄位，但在最終**標準化決策**時仍可能出錯。
4. **item-level 欄位表現非常穩定**——即使明細表達複雜，模型仍具不錯的結構整理能力。
5. **improved prompt 未帶來提升**——反而由 95.2% 降為 93.6%，故正式採用 baseline。

> **錯誤集中、夾擠界取等號：** 12 筆錯誤且每份至多錯一欄，故 `DocErr = 12/250 = 4.8% = Σφ DErrφ`。純文字情境下錯誤彼此不重疊、集中於單一格式敏感欄位；一旦進入 Level 3，多欄位同時出錯將使此式不再取等號，DocAcc 掉得更快。

---

## 日期標準化支線實驗

針對 `po_date` 格式歧義，測試不同後處理策略。評估同時納入**修正成功數 S** 與**誤修正數 O**：

| 策略 | `po_date` 正確率 | 修正 | 誤修正 | 說明 |
| --- | --- | --- | --- | --- |
| Baseline | 95.2% | — | — | 原始結果 |
| Rule-based fix | 95.2% | 0/12 | 0 | 文件內無足夠線索 |
| Candidate validation | 95.2% | 0/12 | 0 | 缺乏驗證依據 |
| Default `dd/mm` | 92.4% | 11/12 | **18** | 改善力強但副作用大 |
| Default `mm/dd` | **95.6%** | 1/12 | **0** | 改善有限、**穩定性最佳** |

**意涵：** 對格式敏感欄位而言，修正策略不能只看修正了多少錯誤，也必須同時考量是否破壞原本正確的案例（淨變化 =（S − O）/ N）。

---

## 重點結論

- 模型在複雜純文字訂單中仍維持高準確率。
- 主要錯誤集中在 `po_date`，`dd/mm` 與 `mm/dd` 的格式歧義是核心錯誤來源。
- item-level 欄位在本階段表現非常穩定。
- `improved` prompt 未帶來整體提升，baseline 仍是較穩定的正式採用版本。
- 在高異質純文字情境下，模型的主要限制不一定是欄位辨識，而可能是**標準化決策**。

---

## Summary

Level 2 shows that LLM-based extraction remains highly effective in complex text-based order documents. The major limitation is not general field recognition failure, but date standardization ambiguity, especially in the `po_date` field. Baseline remains the officially adopted version at this level.
