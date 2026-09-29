"""Question 3(b) robustness: monthly 1% winsorization of BM and BM_CZ."""

from pathlib import Path
import runpy

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


FIGURE_DIR = Path("figures")
LOWER_QUANTILE = 0.01
UPPER_QUANTILE = 0.99


# Reuse the fully screened, date-linked firm-month sample constructed by the
# primary Q3(b) script, while keeping this robustness analysis in a separate
# runnable file.
base = runpy.run_path("Q3b.py")
merged = base["merged"][["PERMNO", "month", "BM", "BM_CZ"]].copy()


def winsorized_monthly_regression(group: pd.DataFrame) -> pd.Series:
    """Winsorize both signals at monthly 1/99 percentiles, then estimate OLS."""
    bm_lower, bm_upper = group["BM"].quantile([LOWER_QUANTILE, UPPER_QUANTILE])
    cz_lower, cz_upper = group["BM_CZ"].quantile([LOWER_QUANTILE, UPPER_QUANTILE])
    x = group["BM"].clip(bm_lower, bm_upper).to_numpy(dtype=float)
    y = group["BM_CZ"].clip(cz_lower, cz_upper).to_numpy(dtype=float)

    x_centered = x - x.mean()
    y_centered = y - y.mean()
    xx = np.dot(x_centered, x_centered)
    yy = np.dot(y_centered, y_centered)
    if len(group) < 3 or xx <= 0 or yy <= 0:
        return pd.Series(
            {"intercept": np.nan, "slope": np.nan, "R2": np.nan, "N": len(group)}
        )

    xy = np.dot(x_centered, y_centered)
    slope = xy / xx
    return pd.Series(
        {
            "intercept": y.mean() - slope * x.mean(),
            "slope": slope,
            "R2": xy * xy / (xx * yy),
            "N": len(group),
            "BM_p01": bm_lower,
            "BM_p99": bm_upper,
            "BM_CZ_p01": cz_lower,
            "BM_CZ_p99": cz_upper,
        }
    )


results = merged.groupby("month", observed=True).apply(
    winsorized_monthly_regression, include_groups=False
)
results = results.dropna(subset=["intercept", "slope", "R2"]).reset_index()
results["date"] = results["month"].dt.to_timestamp("M")
results.to_csv("q3b_winsorized_monthly_regressions.csv", index=False)

FIGURE_DIR.mkdir(exist_ok=True)
plot_specs = [
    (
        "intercept",
        "Intercept",
        "Monthly Cross-Sectional Regression Intercepts (1% Winsorized)",
        "q3b_winsorized_intercepts.png",
    ),
    (
        "slope",
        "Slope",
        "Monthly Cross-Sectional Regression Slopes (1% Winsorized)",
        "q3b_winsorized_slopes.png",
    ),
    (
        "R2",
        r"$R^2$",
        r"Monthly Cross-Sectional Regression $R^2$ (1% Winsorized)",
        "q3b_winsorized_r2.png",
    ),
]

for column, y_label, title, filename in plot_specs:
    fig, ax = plt.subplots(figsize=(10.5, 4.6))
    ax.plot(results["date"], results[column], color="#8b1a1a", linewidth=1.0)
    ax.axhline(0, color="black", linewidth=0.8, alpha=0.7)
    ax.set_xlabel("Month")
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.xaxis.set_major_locator(mdates.YearLocator(10))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / filename, dpi=300, bbox_inches="tight")
    plt.close(fig)

print("Q3(b) monthly 1% winsorized robustness diagnostics")
print(f"Regression months: {len(results):,}")
print(f"Regression range: {results['month'].iloc[0]} to {results['month'].iloc[-1]}")
print(results[["intercept", "slope", "R2"]].describe().to_string())
