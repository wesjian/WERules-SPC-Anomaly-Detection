# ==========================================
# 🔧 SPC WE Rule Configuration
# ==========================================
# Centralised configuration dataclass for WE Rules (WE1-WE10 + CU1/CU2),
# Record High/Low, and OOC detection.
# Every parameter is exposed as a named field with a sensible default.
# ==========================================

from dataclasses import dataclass


@dataclass
class SPCRuleConfig:
    """Configuration for WE Rules, Record High/Low, and OOC detection.

    All parameters have sensible defaults. Modify individual fields or
    pass a dict to ``from_dict()`` to override.
    """

    # ─── Enable / Disable flags ──────────────────────────────────────
    # WE Rules (Western Electric, UCL/LCL-based)
    en_we1: bool = True          # WE1: last point > UCL
    en_we2: bool = True          # WE2: 2 of 3 > UWL
    en_we3: bool = True          # WE3: 4 of 5 > mean + 1σ
    en_we4: bool = True          # WE4: 8 consecutive > mean
    en_we5: bool = True          # WE5: last point < LCL
    en_we6: bool = True          # WE6: 2 of 3 < LWL
    en_we7: bool = True          # WE7: 4 of 5 < mean - 1σ
    en_we8: bool = True          # WE8: 8 consecutive < mean
    en_we9: bool = True          # WE9: 15 consecutive in 1σ band
    en_we10: bool = True         # WE10: 8 consecutive outside 1σ
    en_cu1: bool = True          # CU1: 7 consecutive increasing
    en_cu2: bool = True          # CU2: 7 consecutive decreasing

    # Record High / Low
    en_rh: bool = True           # Record High
    en_rl: bool = True           # Record Low

    # OOC (Out of Control)
    en_ooc: bool = True
    en_high_ooc: bool = True     # High OOC Rate

    # ─── Sigma ───────────────────────────────────────────────────────
    sigma_divisor: float = 3.0   # σ = (UCL - Target) / divisor

    # ─── WE Rule window sizes ────────────────────────────────────────
    we2_window: int = 3          # WE2: window size
    we2_min_violations: int = 2  # WE2: min violations in window
    we3_window: int = 5          # WE3: window size
    we3_min_violations: int = 4  # WE3: min violations in window
    we4_window: int = 8          # WE4: 8 consecutive
    we6_window: int = 3          # WE6: window size
    we6_min_violations: int = 2  # WE6: min violations in window
    we7_window: int = 5          # WE7: window size
    we7_min_violations: int = 4  # WE7: min violations in window
    we8_window: int = 8          # WE8: 8 consecutive
    we9_window: int = 15         # WE9: 15 consecutive
    we9_min_unique: int = 2      # WE9: min unique values to check
    we10_window: int = 8         # WE10: 8 consecutive
    cu_window: int = 7           # CU1/CU2: 7 consecutive

    # ─── OOC Thresholds ──────────────────────────────────────────────
    ooc_ratio_threshold: float = 0.05  # OOC ratio threshold (5%)
    ooc_min_count: int = 2             # Minimum OOC count to trigger

    @classmethod
    def from_dict(cls, d: dict) -> "SPCRuleConfig":
        """Create a config from a (possibly partial) dict; unknown keys are
        silently ignored so you can pass a superset."""
        valid = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in d.items() if k in valid})

    def to_dict(self) -> dict:
        """Serialize to a plain dict (useful for JSON round-trips)."""
        from dataclasses import asdict
        return asdict(self)
