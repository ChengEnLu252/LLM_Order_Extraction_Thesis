# Level 3 — Image Documents

## 研究定位

Level 3 為本研究的第三個實驗層級，目的在於評估大型語言模型在**影像型訂單文件**中的關鍵資訊擷取能力。

本階段延續 Level 2 的複雜訂單內容，但將文件形式由純文字擴展為影像，並比較兩條方法路線：**OCR-based pipeline** 與 **Vision Direct pipeline**。以 Level 2 內容轉製影像，可**分離**「內容複雜度」與「影像化困難」兩個因素。

Level 3 的重點不只是觀察影像條件下整體準確率是否下降，而是回答：

- 訂單由純文字轉為影像後，整體表現如何變化、錯誤分布如何遷移
- OCR 轉寫後再交由 LLM 抽取，是否仍具可用性
- 能否直接將影像輸入多模態 LLM 而不經 OCR
- 在異質訂單情境下，OCR 是否仍為必要步驟
- OCR 引入的代表性錯誤，能否透過輕量後處理改善

---

## 影像條件與兩條 pipeline

正式實驗僅納入兩種影像版本：

- **clean**：版面乾淨、近似理想掃描
- **v1**：加入較貼近實務的影像干擾（輕度退化）

> 註：其他影像版本曾作額外測試，但**不納入正式論文分析與正式結果**。

兩條 pipeline：

| 路線 | 流程 | 用途 |
| --- | --- | --- |
| **OCR-based** | `image → resize → OCR → OCR text → LLM → JSON` | 文字作為中介表示，銜接純文字流程 |
| **Vision Direct** | `image → multimodal LLM → JSON` | 不經 OCR、端到端擷取 |

兩條 pipeline × 兩種品質，用以分離 **OCR 誤差**與**模型本身限制**。

---

## 抽取欄位（Schema）

Level 3 與其他層級共用相同 schema（見 `schema.json`）：

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

延續前兩層級的 prompt 設計：OCR-based 比較 `baseline` / `improved`，Vision Direct 比較 `baseline_vision` / `improved_vision`。此外依 OCR-based 主實驗結果，額外設計 **OCR 字元混淆修正支線**，分析 `po_number`、`part_number` 等格式規律較強的欄位能否透過輕量後處理顯著改善。

---

## 資料夾結構

```text
Level3/
├── dataset/     # 影像資料、OCR 輸出、metadata 與中間資料
├── scripts/     # 影像生成、OCR、Vision Direct、抽取、評估與分析程式
├── result/      # OCR-based / Vision Direct 的 baseline / improved 結果
├── reports/     # document / field accuracy、error report、正式報告
├── schema.json  # 正式使用的抽取 schema
└── README.md
```

---

## 正式實驗結果

### OCR-based

| 影像 | Prompt | Document Accuracy |
| --- | --- | --- |
| clean | **Baseline（正式採用）** | 86.8%（217/250） |
| clean | Improved | 85.6%（214/250） |
| v1 | **Baseline（正式採用）** | 82.8%（207/250） |
| v1 | Improved | 77.2%（193/250） |

### Vision Direct

| 影像 | Prompt | Document Accuracy |
| --- | --- | --- |
| clean | baseline_vision | 1.2%（3/250） |
| v1 | baseline_vision | 0.8%（2/250） |

> **正式結論：** Vision Direct 僅作比較用途，在本研究設定下幾乎不可用。

### 跨層級對照（baseline）

| Level 2 純文字 | OCR clean | OCR v1 | Vision clean | Vision v1 |
| --- | --- | --- | --- | --- |
| 95.2% | 86.8% | 82.8% | 1.2% | 0.8% |

---

## OCR-based 代表性觀察

相較 Level 2 純文字，整體表現明顯下降但**仍具實際可用性**。錯誤由 Level 2 的**單一日期問題**擴展為三個層次：

| 錯誤層次 | 代表欄位 |
| --- | --- |
| 日期標準化 | `po_date`（歧義未消失） |
| 字元辨識 | `po_number`、`part_number` |
| 行列結構破壞 | item-level 數值對應錯位 |

**資訊分散型（B 類）最脆弱**——B 類本就需要跨區塊整合資訊，影像經 OCR 後若文字破碎、欄位黏連或區塊邊界弱化，模型更難還原完整欄位：

| B 類 DocAcc | Level 2 | OCR clean | OCR v1 | Vision |
| --- | --- | --- | --- | --- |
| | 90% | 64% | 40% | 0% |

`baseline` prompt 仍是較穩定版本。

---

## OCR 字元混淆支線結果

對 `po_number`／`part_number` 施加 **uppercase normalization + pattern-based correction**：

| 影像 | Baseline | + 字元修正 |
| --- | --- | --- |
| clean | 86.8% | **93.6%** |
| v1 | 82.8% | **93.2%** |

主要觀察：

- `po_number` 在 clean 與 v1 條件下皆提升至 **100.0%**，且**未觀察到明顯誤修正**（合法真值為修正算子之不動點 ⇒ 誤修正 O = 0）。
- OCR error propagation 並非完全不可控；對格式規律明確的欄位，欄位導向的輕量後處理可帶來顯著改善。

---

## Vision Direct 代表性觀察

直接將影像輸入多模態 LLM 的 document accuracy 極低。欄位層呈現「**局部看得懂、整體做不好**」：

| 欄位 | 層級 | Vision 正確率 |
| --- | --- | --- |
| `currency` | header | 92% |
| `po_number` | header | 84% |
| `part_number` | item | **8.8%** |

**關鍵解讀：** 問題不在「看不懂影像」，而在無法**同時維持多筆 item-level 的結構一致性**——局部欄位可辨識，但整體 JSON 結構無法穩定維持、多筆明細無法正確對齊，導致 document-level 幾近不可用。`improved_vision` 亦未帶來實質改善。

---

## 重點結論

**OCR-based**

- 相較 Level 2 純文字表現下降，但仍具實際可用性。
- OCR 引入新的字元級錯誤與結構弱化；資訊分散型（B 類）最脆弱。
- `baseline` prompt 較穩定；欄位導向後處理可進一步顯著改善。

**Vision Direct**

- document accuracy 極低；header-level 部分可辨識，item-level 幾乎無法穩定完成。
- 目前無法作為 OCR-based pipeline 的替代方案。

**整體**

- Vision Direct 無法穩定取代 OCR-based pipeline。
- OCR 雖然耗時，但在異質訂單文件的結構化擷取任務中仍是**不可輕易省略的關鍵中介步驟**。

---

## Summary

Level 3 evaluates LLM-based extraction on image-based order documents through two routes: OCR-based and Vision Direct. OCR-based extraction remains usable, though performance drops compared with text-based settings, and field-oriented lightweight post-processing recovers much of the loss. By contrast, Vision Direct performs extremely poorly and cannot reliably replace OCR in this task. This level confirms that OCR is still a critical intermediate step for structured extraction from heterogeneous order document images.
