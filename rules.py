# ==========================================
# 🚨 SPC WE Rules — Rule Functions
# ==========================================
# Pure-function implementations of:
# - WE Rules (WE1-WE10 + CU1/CU2) — UCL/LCL-based
# - OOC (Out of Control) detection
# - Record High / Low detection
#
# No external dependencies beyond numpy and pandas.
# ==========================================

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Optional, Dict, Tuple, NamedTuple

from config import SPCRuleConfig


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Helpers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def calculate_sigma(
    ucl: Optional[float],
    lcl: Optional[float],
    target: Optional[float],
    *,
    sigma_divisor: float = 3.0,
) -> Tuple[float, float]:
    """Compute upper and lower sigma from UCL, LCL, and Target.

    Returns
    -------
    tuple
        ``(sigma_upper, sigma_lower)`` — NaN if any input is invalid.
    """
    if (
        ucl is None or pd.isna(ucl)
        or lcl is None or pd.isna(lcl)
        or target is None or pd.isna(target)
    ):
        return (np.nan, np.nan)
    try:
        sigma_upper = (ucl - target) / sigma_divisor
        sigma_lower = (target - lcl) / sigma_divisor
        return (sigma_upper, sigma_lower)
    except (TypeError, ValueError):
        return (np.nan, np.nan)


# ─── Result container ─────────────────────────────────────────────────
class DetectionResult(NamedTuple):
    """Container returned by ``detect_all``.

    Each field holds a detection outcome:
    - ``str`` fields: ``'HIGHLIGHT'`` or ``'NO_HIGHLIGHT'``
    - ``bool`` fields: True/False
    - ``dict`` fields: detailed sub-results
    """
    # --- OOC ---
    high_ooc: str
    ooc_count: int
    ooc_ratio: float

    # --- Record High/Low ---
    record_high_low: str
    record_high: bool
    record_low: bool

    # --- WE Rules ---
    we_rules: Dict[str, bool]
    we_any_violated: bool

    # --- Aggregated ---
    overall_highlight: str


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WE Rules (WE1-WE10 + CU1/CU2) — Legacy UCL/LCL-based
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def check_we_rules(
    values: np.ndarray,
    *,
    ucl: Optional[float] = None,
    lcl: Optional[float] = None,
    target: Optional[float] = None,
    characteristic: str = "Nominal",
    config: Optional[SPCRuleConfig] = None,
) -> Dict[str, bool]:
    """Check WE1-WE10 + CU1/CU2 rules based on fixed UCL/LCL/Target.

    All rules operate on the tail of the *values* array (most recent data).

    Rule Descriptions
    -----------------
    - **WE1**: Last point > UCL
    - **WE2**: 2 of 3 most recent > UWL (exempt for Bigger/Smaller/Sigma)
    - **WE3**: 4 of 5 most recent > mean + 1σ
    - **WE4**: 8 consecutive > mean
    - **WE5**: Last point < LCL
    - **WE6**: 2 of 3 most recent < LWL (exempt for Bigger/Smaller/Sigma)
    - **WE7**: 4 of 5 most recent < mean - 1σ
    - **WE8**: 8 consecutive < mean
    - **WE9**: 15 consecutive within ±1σ of mean (excluded if all identical)
    - **WE10**: 8 consecutive outside ±1σ (exempt for Bigger/Smaller/Sigma)
    - **CU1**: 7 consecutive increasing
    - **CU2**: 7 consecutive decreasing

    Parameters
    ----------
    values : ndarray
        Measurement values (ordered chronologically).
    ucl, lcl, target : float or None
        Upper/Lower Control Limits and Target (center line).
    characteristic : str
        ``'Nominal'``, ``'Bigger'``, ``'Smaller'``, or ``'Sigma'``.
    config : SPCRuleConfig or None
        Configuration; uses defaults if *None*.

    Returns
    -------
    dict
        ``{rule_name: violated}`` for WE1~WE10, CU1, CU2.
    """
    if config is None:
        config = SPCRuleConfig()

    vals = pd.Series(np.asarray(values, dtype=float))
    n = len(vals)

    rules: Dict[str, bool] = {
        "WE1": False, "WE2": False, "WE3": False, "WE4": False,
        "WE5": False, "WE6": False, "WE7": False, "WE8": False,
        "WE9": False, "WE10": False, "CU1": False, "CU2": False,
    }

    mean = target
    sigma_upper, sigma_lower = calculate_sigma(ucl, lcl, mean, sigma_divisor=config.sigma_divisor)
    sigma_valid = (
        not pd.isna(sigma_upper) and not pd.isna(sigma_lower)
        and mean is not None and not pd.isna(mean)
    )

    if sigma_valid:
        uwl = mean + 2 * sigma_upper
        lwl = mean - 2 * sigma_lower
    else:
        uwl = np.nan
        lwl = np.nan

    # ── WE1: last point > UCL ─────────────────────────────────────────
    if config.en_we1 and ucl is not None and not pd.isna(ucl) and n >= 1:
        rules["WE1"] = bool(vals.iloc[-1] > ucl)

    # ── WE5: last point < LCL ─────────────────────────────────────────
    if config.en_we5 and lcl is not None and not pd.isna(lcl) and n >= 1:
        rules["WE5"] = bool(vals.iloc[-1] < lcl)

    # ── CU1: 7 consecutive increasing ─────────────────────────────────
    if config.en_cu1 and n >= config.cu_window:
        tail = vals.tail(config.cu_window)
        diffs = tail.diff().dropna()
        rules["CU1"] = bool((diffs > 0).all())

    # ── CU2: 7 consecutive decreasing ─────────────────────────────────
    if config.en_cu2 and n >= config.cu_window:
        tail = vals.tail(config.cu_window)
        diffs = tail.diff().dropna()
        rules["CU2"] = bool((diffs < 0).all())

    if not sigma_valid:
        return rules

    # ── WE2: 2 of 3 > UWL (exempt for Bigger/Smaller/Sigma) ──────────
    if config.en_we2 and n >= config.we2_window:
        if characteristic not in ("Bigger", "Smaller", "Sigma"):
            rules["WE2"] = bool((vals.tail(config.we2_window) > uwl).sum() >= config.we2_min_violations)

    # ── WE3: 4 of 5 > mean + 1σ ──────────────────────────────────────
    if config.en_we3 and n >= config.we3_window:
        threshold_val = mean + sigma_upper
        rules["WE3"] = bool((vals.tail(config.we3_window) > threshold_val).sum() >= config.we3_min_violations)

    # ── WE4: 8 consecutive > mean ─────────────────────────────────────
    if config.en_we4 and n >= config.we4_window:
        rules["WE4"] = bool((vals.tail(config.we4_window) > mean).all())

    # ── WE6: 2 of 3 < LWL (exempt for Bigger/Smaller/Sigma) ──────────
    if config.en_we6 and n >= config.we6_window:
        if characteristic not in ("Bigger", "Smaller", "Sigma"):
            rules["WE6"] = bool((vals.tail(config.we6_window) < lwl).sum() >= config.we6_min_violations)

    # ── WE7: 4 of 5 < mean - 1σ ──────────────────────────────────────
    if config.en_we7 and n >= config.we7_window:
        threshold_val = mean - sigma_lower
        rules["WE7"] = bool((vals.tail(config.we7_window) < threshold_val).sum() >= config.we7_min_violations)

    # ── WE8: 8 consecutive < mean ─────────────────────────────────────
    if config.en_we8 and n >= config.we8_window:
        rules["WE8"] = bool((vals.tail(config.we8_window) < mean).all())

    # ── WE9: 15 consecutive within ±1σ (exclude single-value) ─────────
    if config.en_we9 and n >= config.we9_window:
        tail = vals.tail(config.we9_window)
        if tail.nunique() >= config.we9_min_unique:
            in_band = (tail >= mean - sigma_lower) & (tail <= mean + sigma_upper)
            rules["WE9"] = bool(in_band.all())

    # ── WE10: 8 consecutive outside ±1σ (exempt Bigger/Smaller/Sigma) ─
    if config.en_we10 and n >= config.we10_window:
        if characteristic not in ("Bigger", "Smaller", "Sigma"):
            tail = vals.tail(config.we10_window)
            out_band = (tail < mean - sigma_lower) | (tail > mean + sigma_upper)
            rules["WE10"] = bool(out_band.all())

    return rules


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# OOC — Out of Control
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def check_ooc(
    values: np.ndarray,
    ucl: Optional[float],
    lcl: Optional[float],
    *,
    ratio_threshold: float = 0.05,
    min_count: int = 2,
    enabled: bool = True,
) -> Tuple[str, int, float]:
    """Check OOC with ratio+count threshold.

    Parameters
    ----------
    values : ndarray
        Measurement values.
    ucl, lcl : float or None
        Upper/Lower Control Limits.
    ratio_threshold : float
        OOC ratio threshold (default 0.05 = 5%).
    min_count : int
        Minimum OOC count to trigger (default 2).
    enabled : bool
        Whether OOC check is enabled.

    Returns
    -------
    tuple
        ``(highlight_status, ooc_count, ooc_ratio)``
    """
    if not enabled:
        return ("NO_HIGHLIGHT", 0, 0.0)

    values = np.asarray(values, dtype=float)
    total = len(values)
    if total == 0:
        return ("NO_HIGHLIGHT", 0, 0.0)

    ooc_mask = np.zeros(total, dtype=bool)
    if ucl is not None and not pd.isna(ucl):
        ooc_mask |= values > ucl
    if lcl is not None and not pd.isna(lcl):
        ooc_mask |= values < lcl

    ooc_cnt = int(ooc_mask.sum())
    ooc_ratio = ooc_cnt / total

    if ooc_ratio > ratio_threshold and ooc_cnt > min_count:
        return ("HIGHLIGHT", ooc_cnt, ooc_ratio)
    return ("NO_HIGHLIGHT", ooc_cnt, ooc_ratio)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Record High / Low
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def check_record_high_low(
    current_values: np.ndarray,
    historical_values: np.ndarray,
) -> Dict[str, object]:
    """Determine whether current data sets a new record high or low.

    Parameters
    ----------
    current_values : ndarray
        Current (weekly) measurement values.
    historical_values : ndarray
        Historical (baseline) measurement values.

    Returns
    -------
    dict
        ``record_high`` (bool), ``record_low`` (bool), ``highlight_status`` (str)
    """
    current_values = np.asarray(current_values, dtype=float)
    historical_values = np.asarray(historical_values, dtype=float)

    if len(current_values) == 0 or len(historical_values) == 0:
        return {"record_high": False, "record_low": False, "highlight_status": "NO_HIGHLIGHT"}

    current_max = float(np.nanmax(current_values))
    current_min = float(np.nanmin(current_values))
    hist_max = float(np.nanmax(historical_values))
    hist_min = float(np.nanmin(historical_values))

    record_high = current_max > hist_max
    record_low = current_min < hist_min
    highlight = "HIGHLIGHT" if (record_high or record_low) else "NO_HIGHLIGHT"

    return {
        "record_high": record_high,
        "record_low": record_low,
        "highlight_status": highlight,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Aggregate: detect_all — run all rules at once
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def detect_all(
    baseline_values: np.ndarray,
    weekly_values: np.ndarray,
    *,
    ucl: Optional[float] = None,
    lcl: Optional[float] = None,
    target: Optional[float] = None,
    characteristic: str = "Nominal",
    config: Optional[SPCRuleConfig] = None,
) -> DetectionResult:
    """Run all SPC detection rules (WE + OOC + Record HL) for one chart.

    Parameters
    ----------
    baseline_values : ndarray
        Historical baseline measurement values.
    weekly_values : ndarray
        Current week measurement values.
    ucl, lcl, target : float or None
        Upper/Lower Control Limits and Target.
    characteristic : str
        ``'Nominal'``, ``'Bigger'``, ``'Smaller'``, or ``'Sigma'``.
        Controls Characteristics-dependent exemptions for WE2/WE6/WE10.
    config : SPCRuleConfig or None

    Returns
    -------
    DetectionResult
    """
    if config is None:
        config = SPCRuleConfig()

    baseline_values = np.asarray(baseline_values, dtype=float)
    weekly_values = np.asarray(weekly_values, dtype=float)

    # ── OOC ───────────────────────────────────────────────────────────
    ooc_hl, ooc_cnt, ooc_ratio = check_ooc(
        weekly_values, ucl, lcl,
        ratio_threshold=config.ooc_ratio_threshold,
        min_count=config.ooc_min_count,
        enabled=config.en_high_ooc,
    )

    # ── Record High/Low ───────────────────────────────────────────────
    if config.en_rh or config.en_rl:
        record = check_record_high_low(weekly_values, baseline_values)
    else:
        record = {"record_high": False, "record_low": False, "highlight_status": "NO_HIGHLIGHT"}

    record_hl = record["highlight_status"]
    if not config.en_rh:
        record["record_high"] = False
    if not config.en_rl:
        record["record_low"] = False
    if not config.en_rh and not config.en_rl:
        record_hl = "NO_HIGHLIGHT"

    # ── WE Rules ──────────────────────────────────────────────────────
    combined_values = np.concatenate([baseline_values, weekly_values])
    we_rules = check_we_rules(
        combined_values,
        ucl=ucl, lcl=lcl, target=target,
        characteristic=characteristic,
        config=config,
    )
    we_any = any(we_rules.values())

    # ── Overall highlight ─────────────────────────────────────────────
    any_highlight = (
        ooc_hl == "HIGHLIGHT"
        or record_hl == "HIGHLIGHT"
        or we_any
    )
    overall = "HIGHLIGHT" if any_highlight else "NO_HIGHLIGHT"

    return DetectionResult(
        high_ooc=ooc_hl,
        ooc_count=ooc_cnt,
        ooc_ratio=ooc_ratio,
        record_high_low=record_hl,
        record_high=record["record_high"],
        record_low=record["record_low"],
        we_rules=we_rules,
        we_any_violated=we_any,
        overall_highlight=overall,
    )
