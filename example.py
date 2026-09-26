"""
SPC WE Rules Anomaly Detection — Runnable Example Script

Demonstrates WE1-WE10, CU1/CU2, Record High/Low, and OOC detection
with fully configurable parameters.
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from detector import SPCRuleDetector
from config import SPCRuleConfig

np.random.seed(42)


def print_section(title):
    print("\n" + "=" * 60)
    print(f" {title} ")
    print("=" * 60)


def run_nominal_example():
    print_section("Scenario 1: Nominal (Double-sided limits)")

    baseline = np.random.normal(loc=10.0, scale=0.5, size=200)
    weekly = np.random.normal(loc=10.45, scale=0.5, size=25)

    config = SPCRuleConfig(ooc_ratio_threshold=0.05)
    detector = SPCRuleDetector(config=config)

    report = detector.detect(
        baseline_values=baseline,
        weekly_values=weekly,
        ucl=11.5, lcl=8.5, target=10.0,
        characteristic="Nominal",
    )

    print(f"Triggered Rules: {report.triggered_rules()}")
    print(f"WE Rules String:  {report.we_rule_string()}")
    print(f"Overall: {report.result.overall_highlight}")
    d = report.to_dict()
    print(f"OOC Count: {d['ooc_count']} (Ratio: {d['ooc_ratio']:.2%})")
    print(f"Record High: {d['record_high']}, Record Low: {d['record_low']}")


def run_bigger_example():
    print_section("Scenario 2: Bigger is Better (Exemptions)")

    baseline = np.random.normal(loc=10.0, scale=0.5, size=200)

    detector = SPCRuleDetector()

    # Upward shift (GOOD for Bigger → WE2/WE6/WE10 exempted)
    weekly_up = np.random.normal(loc=10.6, scale=0.5, size=25)
    report_up = detector.detect(
        baseline_values=baseline, weekly_values=weekly_up,
        ucl=11.5, lcl=8.5, target=10.0,
        characteristic="Bigger",
    )
    print(f"Upward Shift: {report_up.triggered_rules()} → {report_up.result.overall_highlight}")

    # Downward shift (BAD for Bigger)
    weekly_down = np.random.normal(loc=9.3, scale=0.5, size=25)
    report_down = detector.detect(
        baseline_values=baseline, weekly_values=weekly_down,
        ucl=11.5, lcl=8.5, target=10.0,
        characteristic="Bigger",
    )
    print(f"Downward Shift: {report_down.triggered_rules()} → {report_down.result.overall_highlight}")


def run_custom_params_example():
    print_section("Scenario 3: Custom WE Rule Parameters")

    baseline = np.random.normal(loc=10.0, scale=0.5, size=200)
    weekly = np.random.normal(loc=10.3, scale=0.5, size=25)

    config = SPCRuleConfig(
        en_we9=False,         # Disable WE9
        en_we10=False,        # Disable WE10
        we4_window=6,         # WE4: 6 consecutive (default=8)
        cu_window=5,          # CU: 5 consecutive (default=7)
        en_rh=True,           # Record High ON
        en_rl=False,          # Record Low OFF
        ooc_ratio_threshold=0.03,  # Stricter OOC threshold
    )

    detector = SPCRuleDetector(config=config)
    report = detector.detect(
        baseline_values=baseline, weekly_values=weekly,
        ucl=11.5, lcl=8.5, target=10.0,
        characteristic="Nominal",
    )

    print(f"Config: en_we9={config.en_we9}, en_we10={config.en_we10}")
    print(f"Config: we4_window={config.we4_window}, cu_window={config.cu_window}")
    print(f"Config: en_rh={config.en_rh}, en_rl={config.en_rl}")
    print(f"Config: ooc_ratio_threshold={config.ooc_ratio_threshold}")
    print(f"Triggered: {report.triggered_rules()}")
    print(f"Record High: {report.result.record_high}, Record Low: {report.result.record_low}")
    print(f"Overall: {report.result.overall_highlight}")
    print(f"\nFull summary:")
    for k, v in report.summary().items():
        print(f"  {k}: {v}")


def run_record_hl_example():
    print_section("Scenario 4: Record High / Low Detection")

    baseline = np.random.normal(loc=10.0, scale=0.3, size=200)
    # Weekly with an extreme high outlier
    weekly = np.append(np.random.normal(loc=10.0, scale=0.3, size=24), [12.5])

    detector = SPCRuleDetector()
    report = detector.detect(
        baseline_values=baseline, weekly_values=weekly,
        ucl=11.5, lcl=8.5, target=10.0,
    )

    print(f"Baseline max: {baseline.max():.3f}, Weekly max: {weekly.max():.3f}")
    print(f"Record High: {report.result.record_high}")
    print(f"Record Low: {report.result.record_low}")
    print(f"Triggered: {report.triggered_rules()}")


if __name__ == "__main__":
    print("Starting WE Rules SPC Anomaly Detection Examples...\n")
    run_nominal_example()
    run_bigger_example()
    run_custom_params_example()
    run_record_hl_example()
    print("\nAll examples finished successfully!")
