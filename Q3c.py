"""Question 3(c): CZ-signal decile portfolios and Newey--West HML tests."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


DATA_DIR = Path("Q3_Datasets")
FIGURE_DIR = Path("figures")
START_MONTH = pd.Period("1963-06", freq="M")
SIGNALS = {"BMCZ": "BMdec", "MOMCZ": "Mom12m", "GPCZ": "GP"}
COLORS = {"BMCZ": "#0066cc", "MOMCZ": "#d62728", "GPCZ": "#2ca02c"}
METHODS = {
    "vw_annual_nyse": ("Value-weighted, annual, NYSE breakpoints", "vw"),
    "ew_annual_nyse": ("Equal-weighted, annual, NYSE breakpoints", "ew"),
    "vw_monthly_nyse": ("Value-weighted, monthly, NYSE breakpoints", "vw"),
    "vw_annual_general": ("Value-weighted, annual, general breakpoints", "vw"),
    "ew_monthly_general": ("Equal-weighted, monthly, general breakpoints", "ew"),
}


def load_signal(filename: str, source: str, target: str) -> pd.DataFrame:
    frame = pd.read_csv(DATA_DIR / filename, usecols=["permno", "yyyymm", source])
    for column in ["permno", "yyyymm", source]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna().rename(columns={"permno": "PERMNO", source: target})
    frame[["PERMNO", "yyyymm"]] = frame[["PERMNO", "yyyymm"]].astype("int64")
    return frame.drop_duplicates(["PERMNO", "yyyymm"], keep="last")


def assign_deciles(group: pd.DataFrame, signal: str, nyse: bool) -> pd.Series:
    reference = group.loc[group["EXCHCD"].eq(1), signal] if nyse else group[signal]
    reference = reference.dropna().to_numpy(dtype=float)
    if reference.size < 10:
        return pd.Series(np.nan, index=group.index)
    cutoffs = np.quantile(reference, np.arange(0.1, 1.0, 0.1))
    values = group[signal].to_numpy(dtype=float)
    deciles = np.searchsorted(cutoffs, values, side="right") + 1
    return pd.Series(deciles, index=group.index, dtype="int8")


def portfolio_returns(frame: pd.DataFrame, signal: str, weight: str) -> pd.DataFrame:
    usable = frame.dropna(subset=["decile", "RET"] + (["lag_ME"] if weight == "vw" else [])).copy()
    if weight == "vw":
        usable = usable.loc[usable["lag_ME"].gt(0)]
        usable["weighted_return"] = usable["RET"] * usable["lag_ME"]
        result = usable.groupby(["month", "decile"], observed=True).agg(
            numerator=("weighted_return", "sum"), denominator=("lag_ME", "sum"), n=("RET", "size")
        )
        result["return"] = result["numerator"] / result["denominator"]
    else:
        result = usable.groupby(["month", "decile"], observed=True).agg(
            return_=("RET", "mean"), n=("RET", "size")
        ).rename(columns={"return_": "return"})
    return result.reset_index()[["month", "decile", "return", "n"]]


def nw94_lag(values: np.ndarray) -> int:
    """NW (1994) Bartlett plug-in bandwidth using its AR(1) pilot constant."""
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    if x.size < 3:
        return 0
    centered = x - x.mean()
    denominator = np.dot(centered[:-1], centered[:-1])
    rho = 0.0 if denominator <= 0 else np.dot(centered[1:], centered[:-1]) / denominator
    rho = float(np.clip(rho, -0.97, 0.97))
    alpha = 4.0 * rho * rho / ((1.0 - rho) ** 4)
    constant = 1.1447 * alpha ** (1.0 / 3.0)
    return int(np.clip(np.floor(constant * x.size ** (1.0 / 3.0)), 0, x.size - 1))


def mean_nw_test(values: pd.Series) -> tuple[float, float, int, int]:
    x = values.dropna().to_numpy(dtype=float)
    n = x.size
    lag = nw94_lag(x)
    u = x - x.mean()
    long_run_variance = np.dot(u, u) / n
    for ell in range(1, lag + 1):
        gamma = np.dot(u[ell:], u[:-ell]) / n
        long_run_variance += 2.0 * (1.0 - ell / (lag + 1.0)) * gamma
    se = np.sqrt(max(long_run_variance, 0.0) / n)
    t_stat = x.mean() / se if se > 0 else np.nan
    return float(x.mean()), float(t_stat), n, lag


# Inner-merge the three CZ signals by stock and month.
signals = load_signal("BMdec.csv", "BMdec", "BMCZ")
signals = signals.merge(load_signal("Mom12m.csv", "Mom12m", "MOMCZ"), on=["PERMNO", "yyyymm"])
signals = signals.merge(load_signal("GP.csv", "GP", "GPCZ"), on=["PERMNO", "yyyymm"])

# CRSP universe, returns, market equity, and strictly lagged market equity.
crsp = pd.read_csv(
    DATA_DIR / "CRSP_monthly.csv",
    usecols=["PERMNO", "date", "SHRCD", "EXCHCD", "SICCD", "PRC", "RET", "SHROUT"],
    low_memory=False,
)
crsp["date"] = pd.to_datetime(crsp["date"], errors="coerce")
crsp["month"] = crsp["date"].dt.to_period("M")
for column in ["PERMNO", "SHRCD", "EXCHCD", "SICCD", "PRC", "RET", "SHROUT"]:
    crsp[column] = pd.to_numeric(crsp[column], errors="coerce")
crsp["ME"] = crsp["PRC"].abs() * crsp["SHROUT"]
crsp = crsp.sort_values(["PERMNO", "month"]).drop_duplicates(["PERMNO", "month"], keep="last")
previous_month = crsp.groupby("PERMNO", sort=False)["month"].shift(1)
crsp["lag_ME"] = crsp.groupby("PERMNO", sort=False)["ME"].shift(1).where(
    crsp["month"].astype("int64").sub(previous_month.astype("int64")).eq(1)
)
eligible = (
    crsp["month"].ge(START_MONTH)
    & crsp["SHRCD"].isin([10, 11])
    & crsp["EXCHCD"].isin([1, 2, 3])
    & ~crsp["SICCD"].between(4900, 4949, inclusive="both")
    & ~crsp["SICCD"].between(6000, 6999, inclusive="both")
)
crsp = crsp.loc[eligible].copy()
crsp["yyyymm"] = crsp["month"].dt.year * 100 + crsp["month"].dt.month
panel = crsp.merge(signals, on=["PERMNO", "yyyymm"], how="inner", validate="one_to_one")

# Monthly formation: signals and exchange status at t determine returns at t+1.
monthly_formation = panel[["PERMNO", "month", "EXCHCD", *SIGNALS]].copy()
monthly_formation["month"] += 1
monthly_holdings = panel[["PERMNO", "month", "RET", "lag_ME"]].merge(
    monthly_formation, on=["PERMNO", "month"], how="inner", validate="one_to_one"
)

# Annual formation: June signals determine returns from July through next June.
june = panel.loc[panel["month"].dt.month.eq(6), ["PERMNO", "month", "EXCHCD", *SIGNALS]].copy()
june["formation_year"] = june["month"].dt.year
annual_holdings = panel[["PERMNO", "month", "RET", "lag_ME"]].copy()
annual_holdings["formation_year"] = np.where(
    annual_holdings["month"].dt.month.ge(7),
    annual_holdings["month"].dt.year,
    annual_holdings["month"].dt.year - 1,
)
annual_holdings = annual_holdings.merge(
    june.drop(columns="month"), on=["PERMNO", "formation_year"], how="inner", validate="many_to_one"
)

all_returns = []
for method, (label, weight) in METHODS.items():
    annual = "annual" in method
    nyse = "nyse" in method
    holdings = annual_holdings.copy() if annual else monthly_holdings.copy()
    formation_key = "formation_year" if annual else "month"
    for signal in SIGNALS:
        holdings["decile"] = holdings.groupby(formation_key, group_keys=False, observed=True).apply(
            assign_deciles, signal=signal, nyse=nyse, include_groups=False
        )
        returns = portfolio_returns(holdings, signal, weight)
        returns["method"] = method
        returns["method_label"] = label
        returns["signal"] = signal
        all_returns.append(returns)

portfolio = pd.concat(all_returns, ignore_index=True)

# Fama--French monthly risk-free rate (the source file also contains annual rows).
ff = pd.read_csv(DATA_DIR / "fama_french.csv", skiprows=3)
ff = ff.rename(columns={ff.columns[0]: "yyyymm"})
ff["yyyymm"] = pd.to_numeric(ff["yyyymm"], errors="coerce")
ff["RF"] = pd.to_numeric(ff["RF"], errors="coerce") / 100.0
ff = ff.loc[ff["yyyymm"].between(100000, 999999), ["yyyymm", "RF"]]
ff["month"] = pd.PeriodIndex(ff["yyyymm"].astype(int).astype(str), freq="M")
portfolio = portfolio.merge(ff[["month", "RF"]], on="month", how="inner", validate="many_to_one")
portfolio["excess_return"] = portfolio["return"] - portfolio["RF"]
portfolio.to_csv("q3c_decile_returns.csv", index=False)

# Five scatterplots, each containing the three CZ signals.
FIGURE_DIR.mkdir(exist_ok=True)
averages = portfolio.groupby(["method", "method_label", "signal", "decile"], observed=True)[
    "excess_return"
].mean().reset_index()
for method, (label, _) in METHODS.items():
    subset = averages.loc[averages["method"].eq(method)]
    fig, ax = plt.subplots(figsize=(8.2, 5.0))
    for signal in SIGNALS:
        points = subset.loc[subset["signal"].eq(signal)].sort_values("decile")
        ax.scatter(points["decile"], points["excess_return"] * 100, color=COLORS[signal], label=signal, s=42)
    ax.set_xticks(range(1, 11))
    ax.set_xlabel("Decile")
    ax.set_ylabel("Average monthly excess return (percent)")
    ax.set_title(label)
    ax.grid(True, alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / f"q3c_{method}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

# HML is decile 10 minus decile 1; RF cancels but aligned excess returns are used.
wide = portfolio.pivot(index="month", columns=["method", "method_label", "signal", "decile"], values="excess_return")
summary_rows = []
for method, (label, _) in METHODS.items():
    for signal in SIGNALS:
        hml = wide[(method, label, signal, 10)] - wide[(method, label, signal, 1)]
        mean, t_stat, n, lag = mean_nw_test(hml)
        summary_rows.append({
            "method": method, "method_label": label, "signal": signal,
            "mean_monthly_return": mean, "nw_t_stat": t_stat, "observations": n, "nw_lag": lag,
        })
summary = pd.DataFrame(summary_rows)
summary.to_csv("q3c_hml_summary.csv", index=False)

print(f"Eligible merged firm-months: {len(panel):,}")
print(f"Portfolio-return rows: {len(portfolio):,}")
print(summary.to_string(index=False, formatters={"mean_monthly_return": "{:.6f}".format, "nw_t_stat": "{:.3f}".format}))
