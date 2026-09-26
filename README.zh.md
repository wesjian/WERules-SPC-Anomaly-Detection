# WE Rules SPC 異常偵測

> **Western Electric (WE) Rules**（WE1–WE10 + CU1/CU2）、**Record High/Low** 及 **OOC** 偵測模組 — 所有細部參數皆可調整。

📖 **其他語言**: [English](README.md) | [日本語](README.ja.md)

## 功能概覽

| 分類 | 規則 | 說明 |
|---|---|---|
| **WE Rules** | WE1–WE10, CU1, CU2 | 基於 UCL/LCL/Target 的 Western Electric / Nelson 規則 |
| **Record High/Low** | RH, RL | 偵測是否超越歷史最高/最低值 |
| **OOC** | High OOC | Out-of-Control 比率偵測（ratio + count 門檻） |

---

## 安裝

```bash
# 直接使用，不需 pip install
git clone <repo-url>
cd WERules-SPC-Anomaly-Detection

# 依賴套件: numpy, pandas
pip install numpy pandas
```

---

## 快速上手

```python
import numpy as np
from detector import SPCRuleDetector
from config import SPCRuleConfig

# 1. 建立設定（所有參數都有合理的預設值）
config = SPCRuleConfig()

# 2. 建立偵測器
detector = SPCRuleDetector(config=config)

# 3. 執行偵測
baseline = np.random.normal(loc=10.0, scale=0.5, size=200)
weekly = np.random.normal(loc=10.5, scale=0.5, size=25)

report = detector.detect(
    baseline_values=baseline,
    weekly_values=weekly,
    ucl=11.5, lcl=8.5, target=10.0,
    characteristic="Nominal",
)

# 4. 查看結果
print(report.triggered_rules())        # ['WE4', 'Record High/Low']
print(report.we_rule_string())          # 'WE3, WE4'
print(report.result.overall_highlight)  # 'HIGHLIGHT' or 'NO_HIGHLIGHT'
```

---

## WE Rules 參考表（WE1–WE10 + CU1/CU2）

| 規則 | 說明 | 可調參數 | 豁免條件 |
|---|---|---|---|
| **WE1** | 最後一點 > UCL | — | 無 |
| **WE2** | 最近 3 點中有 2 點 > UWL（2σ） | `we2_window=3`, `we2_min_violations=2` | Bigger/Smaller/Sigma 豁免 |
| **WE3** | 最近 5 點中有 4 點 > mean + 1σ | `we3_window=5`, `we3_min_violations=4` | 無 |
| **WE4** | 連續 8 點 > mean | `we4_window=8` | 無 |
| **WE5** | 最後一點 < LCL | — | 無 |
| **WE6** | 最近 3 點中有 2 點 < LWL（2σ） | `we6_window=3`, `we6_min_violations=2` | Bigger/Smaller/Sigma 豁免 |
| **WE7** | 最近 5 點中有 4 點 < mean - 1σ | `we7_window=5`, `we7_min_violations=4` | 無 |
| **WE8** | 連續 8 點 < mean | `we8_window=8` | 無 |
| **WE9** | 連續 15 點落在 ±1σ 內 | `we9_window=15`, `we9_min_unique=2` | 所有值相同時排除 |
| **WE10** | 連續 8 點落在 ±1σ 外 | `we10_window=8` | Bigger/Smaller/Sigma 豁免 |
| **CU1** | 連續 7 點遞增 | `cu_window=7` | 無 |
| **CU2** | 連續 7 點遞減 | `cu_window=7` | 無 |

### Sigma 計算公式

```
σ_upper = (UCL - Target) / sigma_divisor   # 預設 divisor = 3.0
σ_lower = (Target - LCL) / sigma_divisor
UWL = Target + 2 × σ_upper
LWL = Target - 2 × σ_lower
```

---

## Record High / Low

偵測當前（weekly）資料是否創下歷史新高或新低：

- **Record High**: `max(weekly) > max(baseline)` → HIGHLIGHT
- **Record Low**: `min(weekly) < min(baseline)` → HIGHLIGHT

可獨立啟用/停用：

```python
config = SPCRuleConfig(
    en_rh=True,   # 啟用 Record High 偵測
    en_rl=False,  # 停用 Record Low 偵測
)
```

---

## OOC（Out of Control）

偵測超出管制界線的比率：

```python
config = SPCRuleConfig(
    ooc_ratio_threshold=0.05,  # 超過 5% 才觸發（預設）
    ooc_min_count=2,           # 至少 2 個 OOC 點才觸發（預設）
)
```

---

## 完整參數設定

所有參數都透過 `SPCRuleConfig` 暴露，支援三種建立方式：

```python
# 方法 1: 直接建構
config = SPCRuleConfig(
    en_we1=True,
    we4_window=6,
    ooc_ratio_threshold=0.03,
)

# 方法 2: 從 dict 建立（未知的 key 會被忽略）
config = SPCRuleConfig.from_dict({
    "en_we9": False,
    "cu_window": 5,
})

# 方法 3: 匯出成 dict
d = config.to_dict()
```

### 啟用/停用開關

| 參數 | 預設 | 說明 |
|---|---|---|
| `en_we1` ~ `en_we10` | `True` | 啟用各個 WE 規則 |
| `en_cu1`, `en_cu2` | `True` | 啟用 CU1/CU2 趨勢規則 |
| `en_rh` | `True` | 啟用 Record High 偵測 |
| `en_rl` | `True` | 啟用 Record Low 偵測 |
| `en_ooc`, `en_high_ooc` | `True` | 啟用 OOC 偵測 |

### WE Rule 窗口參數

| 參數 | 預設 | 說明 |
|---|---|---|
| `we2_window` | `3` | WE2: 窗口大小 |
| `we2_min_violations` | `2` | WE2: 窗口內最少違規數 |
| `we3_window` | `5` | WE3: 窗口大小 |
| `we3_min_violations` | `4` | WE3: 窗口內最少違規數 |
| `we4_window` | `8` | WE4: 連續點數 |
| `we6_window` | `3` | WE6: 窗口大小 |
| `we6_min_violations` | `2` | WE6: 窗口內最少違規數 |
| `we7_window` | `5` | WE7: 窗口大小 |
| `we7_min_violations` | `4` | WE7: 窗口內最少違規數 |
| `we8_window` | `8` | WE8: 連續點數 |
| `we9_window` | `15` | WE9: 連續點數 |
| `we9_min_unique` | `2` | WE9: 最少不同值數量 |
| `we10_window` | `8` | WE10: 連續點數 |
| `cu_window` | `7` | CU1/CU2: 連續點數 |
| `sigma_divisor` | `3.0` | σ = (UCL - Target) / divisor |

### OOC 參數

| 參數 | 預設 | 說明 |
|---|---|---|
| `ooc_ratio_threshold` | `0.05` | OOC 比率門檻（5%） |
| `ooc_min_count` | `2` | 最少 OOC 點數 |

---

## Characteristics 豁免機制

`characteristic` 參數控制哪些 WE 規則被豁免：

| Characteristic | WE Rule 豁免 |
|---|---|
| **Nominal** | WE2/WE6/WE10: 正常檢查（不豁免） |
| **Bigger** | WE2/WE6/WE10: 豁免（向上偏移為有利方向） |
| **Smaller** | WE2/WE6/WE10: 豁免（向下偏移為有利方向） |
| **Sigma** | WE2/WE6/WE10: 豁免（同 Smaller） |

---

## 輸出格式

### DetectionReport 方法

| 方法 | 回傳型別 | 說明 |
|---|---|---|
| `triggered_rules()` | `List[str]` | 觸發 HIGHLIGHT 的規則名稱清單 |
| `we_rule_string()` | `str` | 逗號分隔的 WE 違規規則 |
| `summary()` | `Dict[str, str]` | 所有規則的 HIGHLIGHT/NO_HIGHLIGHT 狀態 |
| `to_dict()` | `Dict[str, object]` | 適合 DataFrame 匯出的 flat dict |

### DetectionResult 欄位

```python
result = report.result

# OOC
result.high_ooc           # 'HIGHLIGHT' or 'NO_HIGHLIGHT'
result.ooc_count          # int
result.ooc_ratio          # float

# Record High/Low
result.record_high_low    # 'HIGHLIGHT' or 'NO_HIGHLIGHT'
result.record_high        # bool
result.record_low         # bool

# WE Rules
result.we_rules           # {'WE1': False, 'WE2': True, ...}
result.we_any_violated    # bool

# Overall
result.overall_highlight  # 'HIGHLIGHT' or 'NO_HIGHLIGHT'
```

---

## 專案結構

```
WERules-SPC-Anomaly-Detection/
├── config.py       # SPCRuleConfig — 所有可調參數
├── rules.py        # WE Rules, OOC, Record HL, detect_all()
├── detector.py     # SPCRuleDetector, DetectionReport
├── example.py      # 可執行範例
├── README.md       # 英文文件
├── README.zh.md    # 中文文件
└── README.ja.md    # 日文文件
```

---

## 依賴套件

- **Python** >= 3.9
- **numpy**
- **pandas**

---

## 授權

本專案採用 [GNU General Public License v3.0](LICENSE) 授權。
