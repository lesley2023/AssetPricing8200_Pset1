"""Question 3(b): construct book-to-market and compare it with CZ BMdec."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


CRSP_FILE = Path("Q3_Datasets/CRSP_monthly.csv")
COMPUSTAT_FILE = Path("Q3_Datasets/CRSP_Compustats_Merged.csv")
CZ_FILE = Path("Q3_Datasets/BMdec.csv")
FIGURE_DIR = Path("figures")
START_MONTH = pd.Period("1963-06", freq="M")


# CRSP market equity and the stock universe at each month.
crsp = pd.read_csv(
    CRSP_FILE,
    usecols=["PERMNO", "date", "SHRCD", "EXCHCD", "SICCD", "PRC", "SHROUT"],
    low_memory=False,
)
crsp["date"] = pd.to_datetime(crsp["date"])
crsp["month"] = crsp["date"].dt.to_period("M")
for column in ["PERMNO", "SHRCD", "EXCHCD", "SICCD", "PRC", "SHROUT"]:
    crsp[column] = pd.to_numeric(crsp[column], errors="coerce")
crsp["ME"] = crsp["PRC"].abs() * crsp["SHROUT"]

december_me = crsp.loc[
    crsp["month"].dt.month.eq(12), ["PERMNO", "month", "ME"]
].dropna(subset=["ME"])
december_me["portfolio_year"] = december_me["month"].dt.year + 1
december_me = december_me.drop_duplicates(["PERMNO", "portfolio_year"], keep="last")


# Annual Compustat book equity. Eligibility requires two earlier fiscal years.
comp = pd.read_csv(
    COMPUSTAT_FILE,
    usecols=[
        "GVKEY", "LINKPRIM", "LINKTYPE", "LPERMNO", "LINKDT", "LINKENDDT",
        "datadate", "fyear",
        "at", "ceq", "lt", "pstk", "pstkl", "pstkrv", "seq", "txditc",
    ],
    low_memory=False,
)
for column in [
    "LPERMNO", "fyear", "at", "ceq", "lt", "pstk", "pstkl", "pstkrv",
    "seq", "txditc",
]:
    comp[column] = pd.to_numeric(comp[column], errors="coerce")
for column in ["LINKDT", "LINKENDDT", "datadate"]:
    comp[column] = pd.to_datetime(comp[column], errors="coerce")

comp = comp.dropna(subset=["GVKEY", "datadate", "fyear"]).copy()
comp["accounting_year"] = comp["fyear"].astype(int)
comp["portfolio_year"] = comp["accounting_year"] + 1
comp["june_date"] = pd.to_datetime(comp["portfolio_year"].astype(str) + "-06-30")

# Build accounting history independently of the repeated CRSP link rows. If a
# company has multiple records with one fiscal-year label, retain the latest.
accounting_columns = [
    "GVKEY", "accounting_year", "portfolio_year", "datadate", "at", "ceq",
    "lt", "pstk", "pstkl", "pstkrv", "seq", "txditc",
]
accounting = comp[accounting_columns].drop_duplicates()
accounting = accounting.sort_values(["GVKEY", "accounting_year", "datadate"])
accounting = accounting.drop_duplicates(["GVKEY", "accounting_year"], keep="last")
accounting["prior_fiscal_years"] = accounting.groupby("GVKEY").cumcount()

se = accounting["seq"].combine_first(accounting["ceq"] + accounting["pstk"])
se = se.combine_first(accounting["at"] - accounting["lt"])
preferred = accounting["pstkrv"].combine_first(accounting["pstkl"]).combine_first(
    accounting["pstk"]
)
accounting["BE"] = se + accounting["txditc"].fillna(0.0) - preferred.fillna(0.0)

# Construct a date-specific CCM crosswalk at each June portfolio-formation
# date. LC/LU are valid CRSP links; P/C identify primary/consolidated links.
link_columns = [
    "GVKEY", "portfolio_year", "june_date", "LPERMNO", "LINKDT", "LINKENDDT",
    "LINKTYPE", "LINKPRIM",
]
crosswalk = comp[link_columns].dropna(subset=["LPERMNO"]).drop_duplicates()
link_end = crosswalk["LINKENDDT"].fillna(pd.Timestamp("2099-12-31"))
valid_link = crosswalk["LINKDT"].le(crosswalk["june_date"]) & link_end.ge(
    crosswalk["june_date"]
)
crosswalk = crosswalk.loc[
    valid_link
    & crosswalk["LINKTYPE"].isin(["LC", "LU"])
    & crosswalk["LINKPRIM"].isin(["P", "C"]),
    ["GVKEY", "portfolio_year", "LPERMNO"],
].drop_duplicates()

crosswalk_key = ["GVKEY", "portfolio_year"]
ambiguous = crosswalk.groupby(crosswalk_key)["LPERMNO"].nunique().gt(1)
if ambiguous.any():
    raise ValueError(
        f"Multiple valid primary PERMNOs for {int(ambiguous.sum())} GVKEY-years"
    )
crosswalk = crosswalk.drop_duplicates(crosswalk_key).rename(columns={"LPERMNO": "PERMNO"})

book = accounting.loc[
    accounting["prior_fiscal_years"].ge(2)
    & accounting["BE"].gt(0)
    & accounting["portfolio_year"].ge(1963),
    ["GVKEY", "portfolio_year", "datadate", "BE"],
].merge(crosswalk, on=crosswalk_key, how="inner", validate="one_to_one")
book = book.sort_values("datadate").drop_duplicates(
    ["PERMNO", "portfolio_year"], keep="last"
)

signals = book.merge(
    december_me[["PERMNO", "portfolio_year", "ME"]],
    on=["PERMNO", "portfolio_year"],
    how="inner",
    validate="one_to_one",
)
signals = signals.loc[signals["ME"].gt(0)].copy()
signals["BM"] = signals["BE"] * 1000.0 / signals["ME"]


# A June portfolio-year signal applies from June through the following May.
sample = crsp.loc[crsp["month"].ge(START_MONTH)].copy()
sample["portfolio_year"] = np.where(
    sample["month"].dt.month.ge(6), sample["month"].dt.year, sample["month"].dt.year - 1
)
eligible = (
    sample["SHRCD"].isin([10, 11])
    & sample["EXCHCD"].isin([1, 2, 3])
    & ~sample["SICCD"].between(4900, 4949, inclusive="both")
    & ~sample["SICCD"].between(6000, 6999, inclusive="both")
)
sample = sample.loc[eligible, ["PERMNO", "month", "portfolio_year"]]
sample = sample.merge(
    signals[["PERMNO", "portfolio_year", "BM"]],
    on=["PERMNO", "portfolio_year"],
    how="inner",
    validate="many_to_one",
)
sample["yyyymm"] = sample["month"].dt.year * 100 + sample["month"].dt.month

cz = pd.read_csv(CZ_FILE, usecols=["permno", "yyyymm", "BMdec"])
for column in ["permno", "yyyymm", "BMdec"]:
    cz[column] = pd.to_numeric(cz[column], errors="coerce")
cz["BM_CZ"] = cz["BMdec"]
cz = cz.rename(columns={"permno": "PERMNO"})
cz = cz.drop_duplicates(["PERMNO", "yyyymm"], keep="last")

merged = sample.merge(cz[["PERMNO", "yyyymm", "BM_CZ"]], on=["PERMNO", "yyyymm"])
merged = merged.replace([np.inf, -np.inf], np.nan).dropna(subset=["BM", "BM_CZ"])


def monthly_regression(group: pd.DataFrame) -> pd.Series:
    """OLS of BM_CZ on a constant and constructed BM for one month."""
    x = group["BM"].to_numpy(dtype=float)
    y = group["BM_CZ"].to_numpy(dtype=float)
    x_centered = x - x.mean()
    y_centered = y - y.mean()
    xx = np.dot(x_centered, x_centered)
    yy = np.dot(y_centered, y_centered)
    if len(group) < 3 or xx <= 0 or yy <= 0:
        return pd.Series({"intercept": np.nan, "slope": np.nan, "R2": np.nan, "N": len(group)})
    xy = np.dot(x_centered, y_centered)
    slope = xy / xx
    return pd.Series(
        {
            "intercept": y.mean() - slope * x.mean(),
            "slope": slope,
            "R2": xy * xy / (xx * yy),
            "N": len(group),
        }
    )


results = merged.groupby("month", observed=True).apply(monthly_regression, include_groups=False)
results = results.dropna(subset=["intercept", "slope", "R2"]).reset_index()
results["date"] = results["month"].dt.to_timestamp("M")
results.to_csv("q3b_monthly_regressions.csv", index=False)

FIGURE_DIR.mkdir(exist_ok=True)
plot_specs = [
    ("intercept", "Intercept", "Monthly Cross-Sectional Regression Intercepts", "q3b_intercepts.png"),
    ("slope", "Slope", "Monthly Cross-Sectional Regression Slopes", "q3b_slopes.png"),
    ("R2", r"$R^2$", r"Monthly Cross-Sectional Regression $R^2$", "q3b_r2.png"),
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

print(f"Merged firm-month observations: {len(merged):,}")
print(f"Regression months: {len(results):,}")
print(f"Regression range: {results['month'].iloc[0]} to {results['month'].iloc[-1]}")
print(f"Cross-sectional N range: {int(results['N'].min()):,} to {int(results['N'].max()):,}")
print(results[["intercept", "slope", "R2"]].describe().to_string())
