# 應用大型語言模型於異質訂單文件之關鍵資訊擷取與標準化研究

**Applying Large Language Models for Key Information Extraction and Standardization in Heterogeneous Order Documents**

> 國立政治大學 應用數學系 碩士學位論文實驗專案
> 研究生：呂承恩　·　指導教授：蔡炎龍 博士

本 repository 收錄本論文之完整實驗程式碼、資料與評估報表。研究探討大型語言模型（LLM）在不同文件複雜度與不同輸入型態下，對訂單關鍵資訊「擷取」與「標準化」的表現，並由純文字文件逐步延伸至影像型文件，進一步分析**錯誤發生於哪一層、能否在該層加以修正**。

---

## 目錄

- [研究背景與動機](#研究背景與動機)
- [研究問題](#研究問題)
- [問題形式化框架](#問題形式化框架)
- [統一 Schema](#統一-schema)
- [研究架構](#研究架構)
- [評估方式](#評估方式)
- [正式實驗結果](#正式實驗結果)
- [後處理支線實驗](#後處理支線實驗)
- [研究結論](#研究結論)
- [研究貢獻](#研究貢獻)
- [研究限制與未來方向](#研究限制與未來方向)
- [專案結構](#專案結構)
- [使用工具](#使用工具)

---

## 研究背景與動機

訂單（Purchase Order）是企業交易的起點，連動報價、出貨、請款與庫存，實務上卻常需被**人工讀取、重新鍵入**進 ERP 或訂單管理系統。訂單來源五花八門（Email 內文、PDF 附件、掃描影像、傳真），幾乎沒有統一格式，形成典型的「**同一語意內容、多重表達形式**」多對一結構：

| 語意欄位 | 實務上可能出現的形式 |
| --- | --- |
| 採購單號 | `PO Number`、`Order No.`、`Reference ID`、`P.O.#` |
| 日期 | `2026/03/05`、`05-Mar-26`、`March 5, 2026`、`5/3/26` |
| 金額 | `$1,200.00`、`USD 1200`、`1.200,00` |
| 品項明細 | 條列式 / 表格式 / 半敘述式跨行混排 |

傳統規則式／樣板式方法在**已知版型**上準確又快速，但每出現一種新格式就要新增規則，維護成本隨格式數量線性增長。相對地，LLM 不需事先看過版型，能以**語意推理**處理未見過的格式，對別名、語序、跨行排版具天然容錯性，並可直接輸出結構化 JSON。

但「能不能做」與「做得好不好、錯在哪裡」是兩回事。本研究因此將焦點從「能否抽取」推進到「**錯誤發生於哪一層、能否在該層修正**」，並以嚴謹的分層實驗檢驗，而非僅憑直覺。

---

## 研究問題

1. LLM 在簡單／複雜純文字訂單中，能否**穩定**完成擷取與標準化？
2. 高異質情境下，主要瓶頸落在**欄位辨識**，還是**格式標準化決策**？
3. 後處理機制能否有效修正？修正能力與**過度修正風險**如何權衡？
4. 輸入由文字轉為影像並經 OCR 後，**錯誤分布如何遷移**？
5. 欄位導向的輕量級後處理能否降低 OCR 錯誤傳遞？
6. 直接以多模態模型處理影像，是否足以**取代** OCR-based pipeline？

---

## 問題形式化框架

本研究將擷取系統表述為映射 `f : X → Y`，把實驗現象對應到明確的數學結構：

- **輸入空間 X**：所有可能的訂單表面形式；**輸出空間 Y**：標準化後的結構化結果。
- **語意纖維** `r⁻¹(y) = { x ∈ X : r(x) = y }`：所有「表面相異、語意相同」的文件。纖維既大且雜，即為高度異質——正是本研究的輸入空間特徵。
- **保語意擾動** `τ`（`r(τx) = r(x)`）：Level 2 的五類複雜度，恰對應五族擾動算子（內容語意不變、只改變表面形式）。
- **OCR 通道** `f_ocr = f_txt ∘ T`（先 OCR 再抽取）vs. **Vision Direct** `f_vis`（影像直接送多模態 LLM）：理想下 `T ∘ R = id`，但 `T` **不保語意**——這是 Level 3 較棘手的根本原因。
- **文件錯誤率之夾擠界（命題）**：

  ```
  maxφ DErrφ  ≤  DocErr  ≤  Σφ DErrφ
  ```

  右側取等號 ⇔ 每份文件至多錯一個欄位。此界用來解釋：為何 Level 3 的 DocAcc 下降幅度**大於任一單欄**。
- **零誤修正引理**：當合法真值為修正算子的不動點時，可預先保證誤修正數 `O = 0`（用於 Level 3 OCR 字元修正支線）。

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
```

**標準化原則**

- `po_date` 一律統一為 `YYYY-MM-DD`
- `total_amount`、`unit_price`、`line_amount` 皆輸出為純數值
- 缺漏欄位以 `null` 表示
- `items` 為逐筆明細陣列，不可任意跨列拼接
- 輸出**唯有完全符合規範**才視為合格

---

## 研究架構

本研究分為三個逐步遞進的層級，共用同一套 schema 與評估流程，再針對代表性錯誤另設改善支線：

| 層級 | 文件數 | 內容 | 主要目的 |
| --- | --- | --- | --- |
| **Level 1** — Simple Text | 50 | 低複雜度純文字 | 建立 baseline、驗證 schema 與評估流程 |
| **Level 2** — Complex Text | 250 | 高異質純文字（5 類 × 50） | 分析錯誤型態、比較 prompt |
| **Level 3** — OCR-based | 250 | 影像 → OCR → LLM → JSON | 觀察錯誤結構性遷移（clean / v1） |
| **Level 3** — Vision Direct | 250 | 影像 → 多模態 LLM → JSON | 反向驗證 OCR 的必要性 |

Level 3 直接以 Level 2 內容轉製影像，以**分離**「內容複雜度」與「影像化困難」。

### Level 2 五類複雜度（各 50 份）

| 類別 | 名稱 | 複雜度來源 |
| --- | --- | --- |
| **A** | Field Variation | 別名、語序改變（`Order No.` vs `PO#`） |
| **B** | Scattered Fields | 關鍵欄位散落於不同段落，需跨段整合 |
| **C** | Complex Items | 品項跨行、合併儲存格、半敘述式列法 |
| **D** | Noise Information | 加入 subtotal、tax、shipping fee、條款等雜訊 |
| **E** | Mixed Complexity | 同時包含上述多種來源 |

### Level 3 影像品質與 pipeline

- **影像品質**：`clean`（版面乾淨、近似理想掃描）、`v1`（加入較貼近實務的影像干擾）。
- **兩條 pipeline**：OCR-based（文字作為中介表示，銜接純文字流程）、Vision Direct（不經 OCR，端到端擷取）。
- 兩條 pipeline × 兩種品質，用以分離 **OCR 誤差**與**模型本身限制**。

### Prompt 設計

各層級皆比較兩種 prompt：`baseline`（較簡潔，著重 schema、JSON 輸出與基本標準化規則）與 `improved`（較詳細，額外加入格式限制、OCR 情境說明與判讀規則）。

> **重要觀察：Prompt 並非越複雜越好。** 多數實驗中 baseline 版本反而較穩定。

---

## 評估方式

各階段皆使用以下三類報表進行分析：

- **Document Accuracy** — `DocAcc = #{全部欄位皆正確的文件} / N`。嚴格門檻：一份文件只要任一欄位出錯，整份即判為錯誤（反映整份可用性）。
- **Field Accuracy** — `FieldAccφ = #{欄位 φ 正確的文件} / N`。用以定位錯誤落在哪個欄位。
- **Error Report** — 錯誤欄位、錯誤類型與案例整理。

額外分析：Level 2 category-level analysis、Level 3 OCR-based vs Vision Direct 比較、Level 2 日期歧義支線、Level 3 OCR 字元混淆支線。

---

## 正式實驗結果

### 跨層級總覽（Document Accuracy, baseline）

| 情境 | DocAcc |
| --- | --- |
| Level 1（純文字，簡單） | **100.0%** |
| Level 2（純文字，複雜） | **95.2%** |
| Level 3 OCR-based · clean | **86.8%** |
| Level 3 OCR-based · v1 | **82.8%** |
| Level 3 Vision Direct · clean | **1.2%** |
| Level 3 Vision Direct · v1 | **0.8%** |

純文字穩定 → OCR-based 下降但可用 → Vision Direct 幾近失效。

### Level 1 — 簡單純文字

| Prompt | DocAcc |
| --- | --- |
| **Baseline（正式採用）** | 100.0%（50/50） |
| Improved | 98.0%（49/50） |

證實 schema／流程／評估皆可行，baseline 已足以支撐任務。

### Level 2 — 複雜純文字（250 份）

| Prompt | DocAcc |
| --- | --- |
| **Baseline（正式採用）** | 95.2%（238/250） |
| Improved | 93.6%（234/250） |

Baseline 各類型 DocAcc：**A = 98% · B = 90% · C = 98% · D = 92% · E = 98%**。

**關鍵發現**：其餘欄位皆 100%，12 筆錯誤**全部集中於 `po_date`**，核心原因為 `dd/mm/yyyy` 與 `mm/dd/yyyy` 的日期格式歧義。瓶頸不是欄位辨識失敗，而是**標準化決策歧義**。又因每份至多錯一欄，夾擠界右側取等號：`DocErr = 12/250 = 4.8% = Σφ DErrφ`。

### Level 3 OCR-based

| 影像 | Prompt | DocAcc |
| --- | --- | --- |
| clean | **Baseline（正式採用）** | 86.8%（217/250） |
| clean | Improved | 85.6%（214/250） |
| v1 | **Baseline（正式採用）** | 82.8%（207/250） |
| v1 | Improved | 77.2%（193/250） |

錯誤由 Level 2 的**單一日期問題**擴展為三個層次：日期標準化（`po_date`）、字元辨識（`po_number`、`part_number`）、行列結構破壞（item-level 數值對應錯位）。其中**資訊分散型（B 類）最脆弱**：90% → 64%（clean）→ 40%（v1）。

### Level 3 Vision Direct

| 影像 | DocAcc |
| --- | --- |
| clean | 1.2%（3/250） |
| v1 | 0.8%（2/250） |

欄位層呈現「局部看得懂、整體做不好」：header-level 的 `currency`（92%）、`po_number`（84%）仍具辨識力，但 item-level 的 `part_number` 僅 **8.8%**。問題不在「看不懂影像」，而在無法**同時維持多筆 item-level 的結構一致性**。

> **正式結論：** 在本研究設定下，Vision Direct 幾乎不可用，無法取代 OCR-based pipeline。

---

## 後處理支線實驗

### Level 2 — 日期標準化支線

針對 `po_date` 格式歧義的四種後處理策略。評估同時納入**修正成功數 S** 與**誤修正數 O**（淨變化 =（S − O）/ N）：

| 策略 | `po_date` 正確率 | 修正 | 誤修正 | 說明 |
| --- | --- | --- | --- | --- |
| Baseline | 95.2% | — | — | 原始結果 |
| Rule-based fix | 95.2% | 0/12 | 0 | 文件內無足夠線索 |
| Candidate validation | 95.2% | 0/12 | 0 | 缺乏驗證依據 |
| Default `dd/mm` | 92.4% | 11/12 | **18** | 改善力強但副作用大 |
| Default `mm/dd` | **95.6%** | 1/12 | **0** | 改善有限、**穩定性最佳** |

**研究意涵**：修正成功數高、但誤修正數更高時淨效果為負。評估後處理**必須同時納入 S 與 O**，不能只看修正幅度。

### Level 3 — OCR 字元混淆支線

對 `po_number`／`part_number` 施加 **uppercase normalization + pattern-based correction**：

| 影像 | Baseline DocAcc | + 字元修正 |
| --- | --- | --- |
| clean | 86.8% | **93.6%** |
| v1 | 82.8% | **93.2%** |

`po_number` 在兩條件下皆推升至 **100%**，且**零誤修正**——由零誤修正引理（合法真值為修正算子之不動點 ⇒ O = 0）預先保證。顯示對格式規律明確的欄位，輕量級後處理即可顯著改善，OCR error propagation 並非完全不可控。

---

## 研究結論

1. LLM 在純文字訂單擷取與標準化任務中具備**高度可行性**（Level 1、Level 2）。
2. 複雜純文字下，主要瓶頸是**格式敏感欄位的標準化決策**（`po_date`），而非欄位辨識。
3. 文字轉影像後，錯誤擴展為更廣泛的辨識與結構破壞，但 OCR-based pipeline **仍具實務價值**。
4. 欄位導向的**輕量級後處理**可在不增加模型複雜度下顯著提升結果（且可證零誤修正）。
5. 直接以多模態模型處理影像幾乎不可用，**反向印證 OCR 的必要性**。

---

## 研究貢獻

- **形式化框架**：以語意纖維、保語意擾動、OCR 通道，將實驗對應到明確數學結構（含夾擠界命題、零誤修正引理）。
- **統一比較框架**：以單一 schema 讓純文字／OCR-based／Vision Direct 在同一基準下受檢驗。
- **錯誤來源分解**：明確區分欄位辨識失敗、標準化決策錯誤、OCR 錯誤傳遞。
- **修正策略洞見**：指出後處理評估須同時兼顧改善能力與過度修正風險。
- **實務啟示**：界定現階段 Vision Direct 的能力邊界，確立 OCR 的關鍵中介地位。

---

## 研究限制與未來方向

**研究限制**

- 以合成資料為主，真實文件泛化待驗證。
- schema 聚焦核心欄位。
- 後處理屬輕量範疇；核心模型為 `gpt-4o-mini`。

**未來方向**

- 納入去識別化真實訂單、擴展 schema。
- 結合版面資訊與表格結構，降低 OCR 結構破壞。
- 隨多模態模型演進，重新評估 Vision Direct。

---

## 專案結構

```text
.
├── Level1/          # 簡單純文字訂單實驗（baseline / improved）
├── Level2/          # 複雜純文字訂單實驗（5 類 + 日期標準化支線）
├── Level3/          # 影像型訂單實驗（OCR-based / Vision Direct + 字元修正支線）
├── .gitignore
└── README.md
```

各層級目錄下皆包含 `results/`（模型輸出 JSON）與 `reports/`（評估報表 CSV）。詳細說明見各層級的 `README.md`。

---

## 使用工具

- Python
- OpenAI API / `gpt-4o-mini`
- PaddleOCR
- OpenCV
- 自製 evaluation scripts

---

## 作者

**呂承恩**　國立政治大學 應用數學系（AI / Data Science）
指導教授：蔡炎龍 博士

---

> **Notes.** This repository contains the experimental implementation for the author's master's thesis. The official conclusions are based on the *Level 1 baseline*, *Level 2 baseline*, and *Level 3 OCR-based clean / v1 baselines*. Vision Direct is included for comparison only and is not adopted as a practical solution under the current experimental setting.
