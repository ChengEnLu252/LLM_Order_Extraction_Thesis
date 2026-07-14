# Level 1 — Simple Text Orders

## 研究定位

Level 1 為本研究的第一個實驗層級，目的在於先驗證大型語言模型能否從**簡單、結構明確的純文字訂單文件**中，穩定擷取預先定義的關鍵欄位。

本階段的重點不是追求高複雜度場景下的極限表現，而是建立整體研究的基礎：

- 可用的 schema
- 可行的 extraction pipeline
- 可驗證的 evaluation 流程
- 可作為後續 Level 2 / Level 3 比較基準的 **baseline**

換言之，Level 1 先確認：在低複雜度、低干擾的純文字條件下，資料生成、模型抽取、JSON 輸出與評估流程能否穩定運作。

---

## 資料特性

Level 1 使用 Python 自行生成的純文字訂單資料，每份訂單皆同步建立對應的 ground truth JSON 作為正式評估標準。本層級資料特徵：

- 文件格式單純、欄位名稱固定、整體結構清楚
- 幾乎不含異質性干擾
- 適合作為基礎可行性驗證資料

---

## 抽取欄位（Schema）

Level 1 與其他層級共用相同 schema：

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

標準化原則：`po_date` 統一為 `YYYY-MM-DD`；金額為純數值；缺漏欄位以 `null` 表示。

---

## 實驗內容

本階段比較兩組 prompt——`baseline`（較簡潔）與 `improved`（較高約束、較詳細規則），觀察在簡單純文字場景下兩者是否造成差異。

> **重要觀察：** 即使在簡單情境下，prompt 並非越複雜越好；增加額外規則不一定帶來更穩定的結果。

---

## 資料夾結構

```text
Level1/
├── dataset/   # 純文字訂單資料與對應 ground truth
├── scripts/   # 資料生成、模型抽取、結果評估程式
├── result/    # 模型抽取輸出的 JSON 結果
├── reports/   # 評估報表（document / field accuracy、error report、摘要）
└── README.md
```

---

## 正式實驗結果

Level 1 共使用 **50 份**簡單純文字訂單：

| Prompt | Document Accuracy |
| --- | --- |
| **Baseline（正式採用）** | 100.0%（50/50） |
| Improved | 98.0%（49/50） |

---

## 重點結論

- `baseline` prompt 在本階段表現最穩定。
- `improved` prompt 未帶來提升，反而在個別欄位出現漏抽。
- 成功驗證整體抽取流程可行：schema、資料生成、模型抽取與評估流程皆可穩定運作。
- 本階段建立的 baseline 成為後續 Level 2 與 Level 3 的比較基礎。

---

## Summary

Level 1 confirms that LLM-based extraction is highly feasible for simple text-based order documents. It serves as the foundation of the full thesis pipeline and provides the baseline for subsequent comparisons in Level 2 and Level 3.
