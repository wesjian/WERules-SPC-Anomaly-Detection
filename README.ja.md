# WE Rules SPC 異常検出

> **Western Electric (WE) Rules**（WE1–WE10 + CU1/CU2）、**Record High/Low**、**OOC** 検出モジュール — すべてのパラメータを柔軟に設定可能。

📖 **他の言語**: [English](README.md) | [中文](README.zh.md)

## 機能一覧

| カテゴリ | ルール | 説明 |
|---|---|---|
| **WE Rules** | WE1–WE10, CU1, CU2 | UCL/LCL/Target に基づく Western Electric / Nelson ルール |
| **Record High/Low** | RH, RL | 過去のベースラインと比較し、最高値/最低値の更新を検出 |
| **OOC** | High OOC | 管理限界逸脱率の検出（比率 + カウント閾値） |

---

## インストール

```bash
# そのまま使用可能（pip install 不要）
git clone <repo-url>
cd WERules-SPC-Anomaly-Detection

# 依存パッケージ: numpy, pandas のみ
pip install numpy pandas
```

---

## クイックスタート

```python
import numpy as np
from detector import SPCRuleDetector
from config import SPCRuleConfig

# 1. 設定を作成（すべてのパラメータにデフォルト値あり）
config = SPCRuleConfig()

# 2. 検出器を作成
detector = SPCRuleDetector(config=config)

# 3. 検出を実行
baseline = np.random.normal(loc=10.0, scale=0.5, size=200)
weekly = np.random.normal(loc=10.5, scale=0.5, size=25)

report = detector.detect(
    baseline_values=baseline,
    weekly_values=weekly,
    ucl=11.5, lcl=8.5, target=10.0,
    characteristic="Nominal",
)

# 4. 結果を確認
print(report.triggered_rules())        # ['WE4', 'Record High/Low']
print(report.we_rule_string())          # 'WE3, WE4'
print(report.result.overall_highlight)  # 'HIGHLIGHT' or 'NO_HIGHLIGHT'
```

---

## WE Rules リファレンス（WE1–WE10 + CU1/CU2）

| ルール | 説明 | 設定可能パラメータ | 免除条件 |
|---|---|---|---|
| **WE1** | 最後の点 > UCL | — | なし |
| **WE2** | 直近 3 点中 2 点 > UWL（2σ） | `we2_window=3`, `we2_min_violations=2` | Bigger/Smaller/Sigma で免除 |
| **WE3** | 直近 5 点中 4 点 > mean + 1σ | `we3_window=5`, `we3_min_violations=4` | なし |
| **WE4** | 連続 8 点 > mean | `we4_window=8` | なし |
| **WE5** | 最後の点 < LCL | — | なし |
| **WE6** | 直近 3 点中 2 点 < LWL（2σ） | `we6_window=3`, `we6_min_violations=2` | Bigger/Smaller/Sigma で免除 |
| **WE7** | 直近 5 点中 4 点 < mean - 1σ | `we7_window=5`, `we7_min_violations=4` | なし |
| **WE8** | 連続 8 点 < mean | `we8_window=8` | なし |
| **WE9** | 連続 15 点が ±1σ 以内 | `we9_window=15`, `we9_min_unique=2` | 全値同一の場合は除外 |
| **WE10** | 連続 8 点が ±1σ 外 | `we10_window=8` | Bigger/Smaller/Sigma で免除 |
| **CU1** | 連続 7 点増加 | `cu_window=7` | なし |
| **CU2** | 連続 7 点減少 | `cu_window=7` | なし |

### Sigma 計算式

```
σ_upper = (UCL - Target) / sigma_divisor   # デフォルト divisor = 3.0
σ_lower = (Target - LCL) / sigma_divisor
UWL = Target + 2 × σ_upper
LWL = Target - 2 × σ_lower
```

---

## Record High / Low

現在（weekly）のデータが過去最高値/最低値を更新したかを検出：

- **Record High**: `max(weekly) > max(baseline)` → HIGHLIGHT
- **Record Low**: `min(weekly) < min(baseline)` → HIGHLIGHT

個別に有効/無効を切り替え可能：

```python
config = SPCRuleConfig(
    en_rh=True,   # Record High 検出を有効化
    en_rl=False,  # Record Low 検出を無効化
)
```

---

## OOC（Out of Control）

管理限界を超えるデータ点の比率を検出：

```python
config = SPCRuleConfig(
    ooc_ratio_threshold=0.05,  # 5% 超でトリガー（デフォルト）
    ooc_min_count=2,           # 最低 2 点の OOC が必要（デフォルト）
)
```

---

## 全設定パラメータ

すべてのパラメータは `SPCRuleConfig` で公開。3 つの作成方法：

```python
# 方法 1: 直接構築
config = SPCRuleConfig(
    en_we1=True,
    we4_window=6,
    ooc_ratio_threshold=0.03,
)

# 方法 2: dict から作成（未知のキーは無視）
config = SPCRuleConfig.from_dict({
    "en_we9": False,
    "cu_window": 5,
})

# 方法 3: dict にシリアライズ
d = config.to_dict()
```

### 有効/無効フラグ

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `en_we1` ~ `en_we10` | `True` | 各 WE ルールの有効化 |
| `en_cu1`, `en_cu2` | `True` | CU1/CU2 トレンドルールの有効化 |
| `en_rh` | `True` | Record High 検出の有効化 |
| `en_rl` | `True` | Record Low 検出の有効化 |
| `en_ooc`, `en_high_ooc` | `True` | OOC 検出の有効化 |

### WE Rule ウィンドウパラメータ

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `we2_window` | `3` | WE2: ウィンドウサイズ |
| `we2_min_violations` | `2` | WE2: ウィンドウ内の最小違反数 |
| `we3_window` | `5` | WE3: ウィンドウサイズ |
| `we3_min_violations` | `4` | WE3: ウィンドウ内の最小違反数 |
| `we4_window` | `8` | WE4: 連続点数 |
| `we6_window` | `3` | WE6: ウィンドウサイズ |
| `we6_min_violations` | `2` | WE6: ウィンドウ内の最小違反数 |
| `we7_window` | `5` | WE7: ウィンドウサイズ |
| `we7_min_violations` | `4` | WE7: ウィンドウ内の最小違反数 |
| `we8_window` | `8` | WE8: 連続点数 |
| `we9_window` | `15` | WE9: 連続点数 |
| `we9_min_unique` | `2` | WE9: 最小ユニーク値数 |
| `we10_window` | `8` | WE10: 連続点数 |
| `cu_window` | `7` | CU1/CU2: 連続点数 |
| `sigma_divisor` | `3.0` | σ = (UCL - Target) / divisor |

### OOC パラメータ

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `ooc_ratio_threshold` | `0.05` | OOC 比率閾値（5%） |
| `ooc_min_count` | `2` | 最小 OOC 点数 |

---

## Characteristics による免除メカニズム

`characteristic` パラメータが WE ルールの免除を制御：

| Characteristic | WE Rule 免除 |
|---|---|
| **Nominal** | WE2/WE6/WE10: 通常チェック（免除なし） |
| **Bigger** | WE2/WE6/WE10: 免除（上方シフトが有利） |
| **Smaller** | WE2/WE6/WE10: 免除（下方シフトが有利） |
| **Sigma** | WE2/WE6/WE10: 免除（Smaller と同様） |

---

## 出力形式

### DetectionReport メソッド

| メソッド | 戻り値 | 説明 |
|---|---|---|
| `triggered_rules()` | `List[str]` | HIGHLIGHT をトリガーしたルール名リスト |
| `we_rule_string()` | `str` | カンマ区切りの違反 WE ルール |
| `summary()` | `Dict[str, str]` | 全ルールの HIGHLIGHT/NO_HIGHLIGHT 状態 |
| `to_dict()` | `Dict[str, object]` | DataFrame 行エクスポート用の flat dict |

### DetectionResult フィールド

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

## プロジェクト構成

```
WERules-SPC-Anomaly-Detection/
├── config.py       # SPCRuleConfig — すべての設定パラメータ
├── rules.py        # WE Rules, OOC, Record HL, detect_all()
├── detector.py     # SPCRuleDetector, DetectionReport
├── example.py      # 実行可能なデモスクリプト
├── README.md       # 英語ドキュメント
├── README.zh.md    # 中国語ドキュメント
└── README.ja.md    # 日本語ドキュメント
```

---

## 依存パッケージ

- **Python** >= 3.9
- **numpy**
- **pandas**

---

## ライセンス

MIT
