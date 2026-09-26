# WE Rules SPC Anomaly Detection

> **Western Electric (WE) Rules** (WE1–WE10 + CU1/CU2), **Record High/Low**, and **OOC** detection module — all parameters fully configurable.

📖 **Other Languages**: [中文](README.zh.md) | [日本語](README.ja.md)

## Features

| Category | Rules | Description |
|---|---|---|
| **WE Rules** | WE1–WE10, CU1, CU2 | Western Electric / Nelson rules based on UCL/LCL/Target |
| **Record High/Low** | RH, RL | Detects new record high or low values vs. historical baseline |
| **OOC** | High OOC | Out-of-Control rate detection (ratio + count threshold) |

---

## Installation

```bash
# Clone and use directly (no pip install needed)
git clone <repo-url>
cd WERules-SPC-Anomaly-Detection

# Dependencies: numpy, pandas only
pip install numpy pandas
```

---

## Quick Start

```python
import numpy as np
from detector import SPCRuleDetector
from config import SPCRuleConfig

# 1. Create config (all params have sensible defaults)
config = SPCRuleConfig()

# 2. Create detector
detector = SPCRuleDetector(config=config)

# 3. Run detection
baseline = np.random.normal(loc=10.0, scale=0.5, size=200)
weekly = np.random.normal(loc=10.5, scale=0.5, size=25)

report = detector.detect(
    baseline_values=baseline,
    weekly_values=weekly,
    ucl=11.5, lcl=8.5, target=10.0,
    characteristic="Nominal",
)

# 4. Check results
print(report.triggered_rules())        # ['WE4', 'Record High/Low']
print(report.we_rule_string())          # 'WE3, WE4'
print(report.result.overall_highlight)  # 'HIGHLIGHT' or 'NO_HIGHLIGHT'
```

---

## WE Rules Reference (WE1–WE10 + CU1/CU2)

| Rule | Description | Configurable Parameters | Exemptions |
|---|---|---|---|
| **WE1** | Last point > UCL | — | None |
| **WE2** | 2 of last 3 > UWL (2σ) | `we2_window=3`, `we2_min_violations=2` | Exempt for Bigger/Smaller/Sigma |
| **WE3** | 4 of last 5 > mean + 1σ | `we3_window=5`, `we3_min_violations=4` | None |
| **WE4** | 8 consecutive > mean | `we4_window=8` | None |
| **WE5** | Last point < LCL | — | None |
| **WE6** | 2 of last 3 < LWL (2σ) | `we6_window=3`, `we6_min_violations=2` | Exempt for Bigger/Smaller/Sigma |
| **WE7** | 4 of last 5 < mean - 1σ | `we7_window=5`, `we7_min_violations=4` | None |
| **WE8** | 8 consecutive < mean | `we8_window=8` | None |
| **WE9** | 15 consecutive within ±1σ | `we9_window=15`, `we9_min_unique=2` | Excluded if all values identical |
| **WE10** | 8 consecutive outside ±1σ | `we10_window=8` | Exempt for Bigger/Smaller/Sigma |
| **CU1** | 7 consecutive increasing | `cu_window=7` | None |
| **CU2** | 7 consecutive decreasing | `cu_window=7` | None |

### Sigma Calculation

```
σ_upper = (UCL - Target) / sigma_divisor   # default divisor = 3.0
σ_lower = (Target - LCL) / sigma_divisor
UWL = Target + 2 × σ_upper
LWL = Target - 2 × σ_lower
```

---

## Record High / Low

Detects whether current (weekly) data sets a new historical record:

- **Record High**: `max(weekly) > max(baseline)` → HIGHLIGHT
- **Record Low**: `min(weekly) < min(baseline)` → HIGHLIGHT

Can be independently enabled/disabled:

```python
config = SPCRuleConfig(
    en_rh=True,   # Enable Record High detection
    en_rl=False,  # Disable Record Low detection
)
```

---

## OOC (Out of Control)

Detects high out-of-control rate based on ratio and count thresholds:

```python
config = SPCRuleConfig(
    ooc_ratio_threshold=0.05,  # Trigger when > 5% (default)
    ooc_min_count=2,           # At least 2 OOC points required (default)
)
```

---

## Full Configuration Reference

All parameters are exposed via `SPCRuleConfig`. Three ways to create:

```python
# Method 1: Direct construction
config = SPCRuleConfig(
    en_we1=True,
    we4_window=6,
    ooc_ratio_threshold=0.03,
)

# Method 2: From dict (unknown keys silently ignored)
config = SPCRuleConfig.from_dict({
    "en_we9": False,
    "cu_window": 5,
})

# Method 3: Serialize to dict
d = config.to_dict()
```

### Enable/Disable Flags

| Parameter | Default | Description |
|---|---|---|
| `en_we1` ~ `en_we10` | `True` | Enable individual WE rules |
| `en_cu1`, `en_cu2` | `True` | Enable CU1/CU2 trend rules |
| `en_rh` | `True` | Enable Record High detection |
| `en_rl` | `True` | Enable Record Low detection |
| `en_ooc`, `en_high_ooc` | `True` | Enable OOC detection |

### WE Rule Window Sizes

| Parameter | Default | Description |
|---|---|---|
| `we2_window` | `3` | WE2: window size |
| `we2_min_violations` | `2` | WE2: min violations in window |
| `we3_window` | `5` | WE3: window size |
| `we3_min_violations` | `4` | WE3: min violations in window |
| `we4_window` | `8` | WE4: consecutive points count |
| `we6_window` | `3` | WE6: window size |
| `we6_min_violations` | `2` | WE6: min violations in window |
| `we7_window` | `5` | WE7: window size |
| `we7_min_violations` | `4` | WE7: min violations in window |
| `we8_window` | `8` | WE8: consecutive points count |
| `we9_window` | `15` | WE9: consecutive points count |
| `we9_min_unique` | `2` | WE9: min unique values to check |
| `we10_window` | `8` | WE10: consecutive points count |
| `cu_window` | `7` | CU1/CU2: consecutive points count |
| `sigma_divisor` | `3.0` | σ = (UCL - Target) / divisor |

### OOC Parameters

| Parameter | Default | Description |
|---|---|---|
| `ooc_ratio_threshold` | `0.05` | OOC ratio threshold (5%) |
| `ooc_min_count` | `2` | Minimum OOC count to trigger |

---

## Characteristics-Based Exemptions

The `characteristic` parameter controls which WE rules are exempted:

| Characteristic | WE Rule Exemption |
|---|---|
| **Nominal** | WE2/WE6/WE10: active (no exemption) |
| **Bigger** | WE2/WE6/WE10: exempt (upward shift is favourable) |
| **Smaller** | WE2/WE6/WE10: exempt (downward shift is favourable) |
| **Sigma** | WE2/WE6/WE10: exempt (same as Smaller) |

---

## Output Format

### DetectionReport Methods

| Method | Returns | Description |
|---|---|---|
| `triggered_rules()` | `List[str]` | Rule names that triggered HIGHLIGHT |
| `we_rule_string()` | `str` | Comma-separated violated WE rules |
| `summary()` | `Dict[str, str]` | All rules with HIGHLIGHT/NO_HIGHLIGHT status |
| `to_dict()` | `Dict[str, object]` | Flat dict suitable for DataFrame row export |

### DetectionResult Fields

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

## Project Structure

```
WERules-SPC-Anomaly-Detection/
├── config.py       # SPCRuleConfig — all configurable parameters
├── rules.py        # WE Rules, OOC, Record HL, detect_all()
├── detector.py     # SPCRuleDetector, DetectionReport
├── example.py      # Runnable demo script
├── README.md       # English documentation
├── README.zh.md    # Chinese documentation
└── README.ja.md    # Japanese documentation
```

---

## Dependencies

- **Python** >= 3.9
- **numpy**
- **pandas**

---

## License

MIT
