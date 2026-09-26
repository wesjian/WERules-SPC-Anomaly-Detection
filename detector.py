# ==========================================
# 🔍 SPC Rule Detector — High-level API
# ==========================================

from __future__ import annotations

import numpy as np
from typing import Optional, Dict, List

from config import SPCRuleConfig
from rules import detect_all, DetectionResult


class SPCRuleDetector:
    """High-level SPC anomaly detector for WE Rules + OOC + Record High/Low.

    Usage
    -----
    >>> from detector import SPCRuleDetector
    >>> from config import SPCRuleConfig
    >>> cfg = SPCRuleConfig(ooc_ratio_threshold=0.05, en_we9=False)
    >>> detector = SPCRuleDetector(config=cfg)
    >>> result = detector.detect(
    ...     baseline_values=baseline_arr,
    ...     weekly_values=weekly_arr,
    ...     ucl=10.5, lcl=9.5, target=10.0,
    ...     characteristic="Nominal",
    ... )
    >>> print(result.summary())
    >>> flagged = result.triggered_rules()
    """

    def __init__(self, config: Optional[SPCRuleConfig] = None):
        self.config = config or SPCRuleConfig()

    def detect(
        self,
        baseline_values: np.ndarray,
        weekly_values: np.ndarray,
        *,
        ucl: Optional[float] = None,
        lcl: Optional[float] = None,
        target: Optional[float] = None,
        characteristic: str = "Nominal",
    ) -> "DetectionReport":
        """Run all rules on the given baseline/weekly data.

        Parameters
        ----------
        baseline_values : ndarray
            Historical baseline measurement values.
        weekly_values : ndarray
            Current week measurement values.
        ucl, lcl, target : float or None
        characteristic : str
            ``'Nominal'``, ``'Bigger'``, ``'Smaller'``, or ``'Sigma'``.

        Returns
        -------
        DetectionReport
        """
        result = detect_all(
            baseline_values,
            weekly_values,
            ucl=ucl, lcl=lcl, target=target,
            characteristic=characteristic,
            config=self.config,
        )
        return DetectionReport(result)


class DetectionReport:
    """Report produced by :meth:`SPCRuleDetector.detect`.

    Provides convenience methods on top of the raw DetectionResult.
    """

    def __init__(self, result: DetectionResult):
        self._result = result

    @property
    def result(self) -> DetectionResult:
        """Access the raw :class:`DetectionResult` named tuple."""
        return self._result

    # ─── Summary ─────────────────────────────────────────────────────
    def summary(self) -> Dict[str, str]:
        """Return ``{rule_label: HIGHLIGHT/NO_HIGHLIGHT}`` for every rule."""
        r = self._result
        out: Dict[str, str] = {}

        # OOC
        out["High OOC"] = r.high_ooc

        # Record High/Low
        out["Record High/Low"] = r.record_high_low

        # WE Rules
        for rule_name, violated in r.we_rules.items():
            out[rule_name] = "HIGHLIGHT" if violated else "NO_HIGHLIGHT"

        # Overall
        out["Overall"] = r.overall_highlight

        return out

    # ─── Triggered rules ─────────────────────────────────────────────
    def triggered_rules(self) -> List[str]:
        """Return list of rule names that triggered HIGHLIGHT."""
        triggered: List[str] = []
        r = self._result

        if r.high_ooc == "HIGHLIGHT":
            triggered.append("High OOC")
        if r.record_high_low == "HIGHLIGHT":
            triggered.append("Record High/Low")

        for rule_name, violated in r.we_rules.items():
            if violated:
                triggered.append(rule_name)

        return triggered

    # ─── WE Rule string ──────────────────────────────────────────────
    def we_rule_string(self) -> str:
        """Comma-separated list of violated WE rules (e.g. 'WE1, WE3, CU1')."""
        violated = [name for name, v in self._result.we_rules.items() if v]
        return ", ".join(violated) if violated else ""

    # ─── To dict ─────────────────────────────────────────────────────
    def to_dict(self) -> Dict[str, object]:
        """Export results as a flat dictionary suitable for DataFrame row."""
        r = self._result
        d: Dict[str, object] = {
            "HL_high_OOC": r.high_ooc,
            "ooc_count": r.ooc_count,
            "ooc_ratio": r.ooc_ratio,
            "HL_record_high_low": r.record_high_low,
            "record_high": r.record_high,
            "record_low": r.record_low,
            "WE_Rule": self.we_rule_string(),
            "highlight_status": r.overall_highlight,
        }
        # Flatten WE rules
        for rule_name, violated in r.we_rules.items():
            d[rule_name] = violated
        return d
