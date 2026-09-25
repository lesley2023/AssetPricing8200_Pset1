"""Question 3(a): compare a CRSP momentum signal with the CZ Mom12m signal."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


CRSP_FILE = Path("Q3_Datasets/CRSP_monthly.csv")
CZ_FILE = Path("Q3_Datasets/Mom12m.csv")
FIGURE_DIR = Path("figures")
START_MONTH = pd.Period("1963-06", freq="M")


# Load only the fields needed for the signal, sample restrictions, and merge.
crsp = pd.read_csv(
    CRSP_FILE,
    usecols=["PERMNO", "date", "SHRCD", "EXCHCD", "SICCD", "RET"],
    low_memory=False,
)
crsp["date"] = pd.to_datetime(crsp["date"])
crsp["month"] = crsp["date"].dt.to_period("M")
crsp["month_number"] = crsp["month"].astype("int64")
for column in ["SHRCD", "EXCHCD", "SICCD", "RET"]:
    crsp[column] = pd.to_numeric(crsp[column], errors="coerce")
crsp = crsp.sort_values(["PERMNO", "month"]).reset_index(drop=True)

# MOM at the end of month tau is the compounded return from tau-12 through
# tau-1. A valid signal requires 12 numeric returns in consecutive months.
by_firm = crsp.groupby("PERMNO", sort=False)
lagged_return = by_firm["RET"].shift(1)
lagged_gross = 1.0 + lagged_return
valid_gross = lagged_gross.notna() & lagged_gross.ge(0.0)
zero_gross = lagged_gross.eq(0.0)
log_gross = np.log(lagged_gross.where(lagged_gross.gt(0.0))).fillna(0.0)

rolling_count = valid_gross.astype("int8").groupby(crsp["PERMNO"], sort=False).rolling(12).sum()
rolling_zeros = zero_gross.astype("int8").groupby(crsp["PERMNO"], sort=False).rolling(12).sum()
rolling_log_sum = log_gross.groupby(crsp["PERMNO"], sort=False).rolling(12).sum()
rolling_count = rolling_count.reset_index(level=0, drop=True)
rolling_zeros = rolling_zeros.reset_index(level=0, drop=True)
rolling_log_sum = rolling_log_sum.reset_index(level=0, drop=True)

lag_12_month = by_firm["month_number"].shift(12)
consecutive_window = crsp["month_number"].sub(lag_12_month).eq(12)
crsp["MOM"] = np.where(
    (rolling_count == 12) & consecutive_window,
    np.where(rolling_zeros.gt(0), -1.0, np.expm1(rolling_log_sum)),
    np.nan,
)

# Apply the requested stock-universe restrictions at the signal month.
eligible = (
    crsp["month"].ge(START_MONTH)
    & crsp["SHRCD"].isin([10, 11])
    & crsp["EXCHCD"].isin([1, 2, 3])
    & ~crsp["SICCD"].between(4900, 4949, inclusive="both")
    & ~crsp["SICCD"].between(6000, 6999, inclusive="both")
)
sample = crsp.loc[eligible, ["PERMNO", "month", "MOM"]].dropna()
sample["yyyymm"] = sample["month"].dt.year * 100 + sample["month"].dt.month

cz = pd.read_csv(CZ_FILE, usecols=["permno", "yyyymm", "Mom12m"])
cz["Mom12m"] = pd.to_numeric(cz["Mom12m"], errors="coerce")
cz = cz.rename(columns={"permno": "PERMNO", "Mom12m": "MOMCZ"})

merged = sample.merge(cz, on=["PERMNO", "yyyymm"], how="inner", validate="one_to_one")
merged = merged.replace([np.inf, -np.inf], np.nan).dropna(subset=["MOM", "MOMCZ"])


def monthly_regression(group: pd.DataFrame) -> pd.Series:
    """OLS of MOMCZ on a constant and MOM for one cross section."""
    x = group["MOM"].to_numpy(dtype=float)
    y = group["MOMCZ"].to_numpy(dtype=float)
    x_mean, y_mean = x.mean(), y.mean()
    x_centered, y_centered = x - x_mean, y - y_mean
    x_scale, y_scale = np.max(np.abs(x_centered)), np.max(np.abs(y_centered))
    if x_scale == 0 or y_scale == 0:
        return pd.Series({"intercept": np.nan, "slope": np.nan, "R2": np.nan, "N": len(group)})
    x_normalized = x_centered / x_scale
    y_normalized = y_centered / y_scale
    xx = np.dot(x_normalized, x_normalized)
    yy = np.dot(y_normalized, y_normalized)
    xy = np.dot(x_normalized, y_normalized)
    slope = (y_scale / x_scale) * xy / xx
    intercept = y_mean - slope * x_mean
    r_squared = (xy * xy) / (xx * yy)
    return pd.Series(
        {"intercept": intercept, "slope": slope, "R2": r_squared, "N": len(group)}
    )


results = merged.groupby("month", observed=True).apply(monthly_regression, include_groups=False)
results = results.dropna(subset=["intercept", "slope", "R2"]).reset_index()
results["date"] = results["month"].dt.to_timestamp("M")
results.to_csv("q3a_monthly_regressions.csv", index=False)

FIGURE_DIR.mkdir(exist_ok=True)
plot_specs = [
    ("intercept", "Intercept", "Monthly Cross-Sectional Regression Intercepts", "q3a_intercepts.png"),
    ("slope", "Slope", "Monthly Cross-Sectional Regression Slopes", "q3a_slopes.png"),
    ("R2", r"$R^2$", r"Monthly Cross-Sectional Regression $R^2$", "q3a_r2.png"),
]

for column, y_label, title, filename in plot_specs:
    fig, ax = plt.subplots(figsize=(10.5, 4.6))
    ax.plot(results["date"], results[column], color="#1f4e79", linewidth=1.0)
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

print("Q3(a) diagnostics")
print(f"Merged firm-month observations: {len(merged):,}")
print(f"Regression months: {len(results):,}")
print(f"First regression month: {results['month'].iloc[0]}")
print(f"Last regression month: {results['month'].iloc[-1]}")
print(f"Cross-sectional N range: {int(results['N'].min()):,} to {int(results['N'].max()):,}")
print("\nCoefficient and R2 summary:")
print(results[["intercept", "slope", "R2"]].describe().to_string())
