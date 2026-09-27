"""Question 3(d): monthly Fama--MacBeth regressions using signal deciles."""

from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path("Q3_Datasets")
OUTPUT_DIR = Path("output")
START_MONTH = pd.Period("1963-06", freq="M")
SIGNALS = ["BM", "GP", "Dur"]
QUANTILES = {signal: f"Q_{signal}" for signal in SIGNALS}
SPECIFICATIONS = {
    1: ["BM"],
    2: ["GP"],
    3: ["Dur"],
    4: ["BM", "GP"],
    5: ["Dur", "BM"],
    6: ["Dur", "GP"],
    7: ["Dur", "BM", "GP"],
}


def load_cz(filename: str, source: str, target: str) -> pd.DataFrame:
    frame = pd.read_csv(DATA_DIR / filename, usecols=["permno", "yyyymm", source])
    for column in ["permno", "yyyymm", source]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna().rename(columns={"permno": "PERMNO", source: target})
    frame[["PERMNO", "yyyymm"]] = frame[["PERMNO", "yyyymm"]].astype("int64")
    return frame.drop_duplicates(["PERMNO", "yyyymm"], keep="last")


def deciles(values: pd.Series) -> pd.Series:
    """Assign 1--10 using cross-sectional empirical-decile cutoffs."""
    valid = values.dropna()
    result = pd.Series(np.nan, index=values.index)
    if valid.size < 10:
        return result
    cutoffs = np.quantile(valid.to_numpy(dtype=float), np.arange(0.1, 1.0, 0.1))
    result.loc[valid.index] = np.searchsorted(cutoffs, valid.to_numpy(dtype=float), side="right") + 1
    return result


def cross_section(group: pd.DataFrame, predictors: list[str], method: str) -> dict:
    columns = [QUANTILES[x] for x in predictors]
    needed = ["next_excess_return", *columns] + (["ME"] if method == "WLS" else [])
    sample = group.dropna(subset=needed)
    if method == "WLS":
        sample = sample.loc[sample["ME"].gt(0)]
    x = np.column_stack([np.ones(len(sample)), sample[columns].to_numpy(dtype=float)])
    y = sample["next_excess_return"].to_numpy(dtype=float)
    if len(sample) <= x.shape[1] or np.linalg.matrix_rank(x) < x.shape[1]:
        return {}
    if method == "WLS":
        root_weight = np.sqrt(sample["ME"].to_numpy(dtype=float))
        coefficients = np.linalg.lstsq(x * root_weight[:, None], y * root_weight, rcond=None)[0]
    else:
        coefficients = np.linalg.lstsq(x, y, rcond=None)[0]
    result = {"intercept": coefficients[0], "nobs": len(sample)}
    result.update({name: value for name, value in zip(predictors, coefficients[1:])})
    return result


def nw94_lag(values: np.ndarray) -> int:
    """NW (1994) Bartlett plug-in bandwidth using the AR(1) pilot constant."""
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


def summarize_coefficients(values: pd.Series) -> dict:
    x = values.dropna().to_numpy(dtype=float)
    months = x.size
    estimate = x.mean()
    conventional_se = x.std(ddof=1) / np.sqrt(months)
    lag = nw94_lag(x)
    residual = x - estimate
    long_run_variance = np.dot(residual, residual) / months
    for ell in range(1, lag + 1):
        gamma = np.dot(residual[ell:], residual[:-ell]) / months
        long_run_variance += 2.0 * (1.0 - ell / (lag + 1.0)) * gamma
    nw_se = np.sqrt(max(long_run_variance, 0.0) / months)
    return {
        "estimate": estimate,
        "conventional_se": conventional_se,
        "conventional_t": estimate / conventional_se if conventional_se > 0 else np.nan,
        "nw_se": nw_se,
        "nw_t": estimate / nw_se if nw_se > 0 else np.nan,
        "nw_lag": lag,
        "months": months,
    }


def tex_number(value: float, decimals: int) -> str:
    formatted = f"{value:.{decimals}f}"
    return f"${formatted}$" if value < 0 else formatted


def write_latex_table(summary: pd.DataFrame, statistic: str, destination: Path) -> None:
    """Write one complete OLS/WLS Fama--MacBeth table fragment."""
    is_nw = statistic == "nw_t"
    caption_suffix = "Newey--West inference" if is_nw else "conventional inference"
    label_suffix = "nw" if is_nw else "conventional"
    lookup = summary.set_index(["method", "specification", "coefficient"])

    def cell(method: str, specification: int, coefficient: str) -> str:
        predictors = ["intercept", *SPECIFICATIONS[specification]]
        if coefficient not in predictors:
            return ""
        row = lookup.loc[(method, specification, coefficient)]
        estimate = tex_number(100.0 * row["estimate"], 4)
        t_stat = tex_number(row[statistic], 2)
        return rf"\fmcell{{{estimate}}}{{{t_stat}}}"

    lines = [
        r"\begin{table}[!htbp]",
        r"    \centering",
        rf"    \caption{{Fama--MacBeth regressions of next-month stock excess returns: {caption_suffix}}}",
        rf"    \label{{tab:q3d_fama_macbeth_{label_suffix}}}",
        r"    \newcommand{\fmcell}[2]{\shortstack{#1\\(#2)}}",
        r"    \resizebox{\textwidth}{!}{%",
        r"    \begin{tabular}{lccccccc}",
        r"        \toprule",
        r"        & (1) & (2) & (3) & (4) & (5) & (6) & (7) \\",
        r"        \midrule",
    ]
    labels = {"intercept": "Intercept", "BM": r"$Q^{BM}$", "GP": r"$Q^{GP}$", "Dur": r"$Q^{Dur}$"}
    for panel, method in [("Panel A: OLS", "OLS"), ("Panel B: WLS", "WLS")]:
        if method == "WLS":
            lines.append(r"        \midrule")
        lines.append(rf"        \multicolumn{{8}}{{l}}{{\textit{{{panel}}}}} \\")
        for coefficient in ["intercept", "BM", "GP", "Dur"]:
            cells = [cell(method, specification, coefficient) for specification in SPECIFICATIONS]
            lines.append(f"        {labels[coefficient]} & " + " & ".join(cells) + r" \\")
        months = [int(lookup.loc[(method, specification, "intercept"), "months"]) for specification in SPECIFICATIONS]
        lines.append("        Months & " + " & ".join(map(str, months)) + r" \\")
    method_note = (
        r"Newey--West (1987, 1994) $t$-statistics with automatically selected lags are in parentheses."
        if is_nw
        else r"Conventional Fama--MacBeth $t$-statistics are in parentheses."
    )
    lines.extend([
        r"        \bottomrule",
        r"    \end{tabular}%",
        r"    }",
        r"",
        r"    \vspace{0.5em}",
        r"    \begin{minipage}{0.98\textwidth}",
        r"    \footnotesize",
        r"    \textit{Notes:} Coefficients are monthly percentage points. $Q^{BM}$, $Q^{GP}$, and $Q^{Dur}$ are monthly cross-sectional deciles from 1 to 10. WLS uses month-$\tau$ market equity as the weight. " + method_note,
        r"    \end{minipage}",
        r"\end{table}",
        r"\FloatBarrier",
        "",
    ])
    destination.write_text("\n".join(lines), encoding="utf-8")


# Monthly CZ signals.
cz = load_cz("BMdec.csv", "BMdec", "BM").merge(
    load_cz("GP.csv", "GP", "GP"), on=["PERMNO", "yyyymm"], how="inner", validate="one_to_one"
)
cz["month"] = pd.PeriodIndex(cz["yyyymm"].astype(str), freq="M")
cz["formation_year"] = np.where(cz["month"].dt.month.ge(6), cz["month"].dt.year, cz["month"].dt.year - 1)

# Duration measured at each June is held from that June through the next May.
duration = pd.read_csv(DATA_DIR / "Dur Dataset.csv", usecols=["PERMNO", "FF.YEAR", "Dur"])
for column in ["PERMNO", "FF.YEAR", "Dur"]:
    duration[column] = pd.to_numeric(duration[column], errors="coerce")
duration = duration.dropna().rename(columns={"FF.YEAR": "formation_year"})
duration[["PERMNO", "formation_year"]] = duration[["PERMNO", "formation_year"]].astype("int64")
if duration.duplicated(["PERMNO", "formation_year"]).any():
    raise ValueError("Duration file contains duplicate PERMNO-year observations")
signals = cz.merge(duration, on=["PERMNO", "formation_year"], how="inner", validate="many_to_one")

# CRSP next-month returns are constructed before applying the formation-month universe screen.
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
by_firm = crsp.groupby("PERMNO", sort=False)
next_month = by_firm["month"].shift(-1)
crsp["next_return"] = by_firm["RET"].shift(-1).where(
    next_month.astype("int64").sub(crsp["month"].astype("int64")).eq(1)
)
eligible = (
    crsp["month"].ge(START_MONTH)
    & crsp["SHRCD"].isin([10, 11])
    & crsp["EXCHCD"].isin([1, 2, 3])
    & ~crsp["SICCD"].between(4900, 4949, inclusive="both")
    & ~crsp["SICCD"].between(6000, 6999, inclusive="both")
)
crsp = crsp.loc[eligible, ["PERMNO", "month", "ME", "next_return"]].copy()
crsp["yyyymm"] = crsp["month"].dt.year * 100 + crsp["month"].dt.month
panel = crsp.merge(signals[["PERMNO", "yyyymm", *SIGNALS]], on=["PERMNO", "yyyymm"], how="inner")

# Attach RF for tau+1 and construct the three contemporaneous signal deciles.
ff = pd.read_csv(DATA_DIR / "fama_french.csv", skiprows=3)
ff = ff.rename(columns={ff.columns[0]: "yyyymm"})
ff["yyyymm"] = pd.to_numeric(ff["yyyymm"], errors="coerce")
ff["RF"] = pd.to_numeric(ff["RF"], errors="coerce") / 100.0
ff = ff.loc[ff["yyyymm"].between(100000, 999999), ["yyyymm", "RF"]]
ff["return_month"] = pd.PeriodIndex(ff["yyyymm"].astype(int).astype(str), freq="M")
panel["return_month"] = panel["month"] + 1
panel = panel.merge(ff[["return_month", "RF"]], on="return_month", how="inner", validate="many_to_one")
panel["next_excess_return"] = panel["next_return"] - panel["RF"]
for signal in SIGNALS:
    panel[QUANTILES[signal]] = panel.groupby("month", observed=True)[signal].transform(deciles)

# Fourteen monthly-regression sets: seven specifications for OLS and WLS.
monthly_rows = []
for method in ["OLS", "WLS"]:
    for specification, predictors in SPECIFICATIONS.items():
        for month, group in panel.groupby("month", observed=True):
            estimates = cross_section(group, predictors, method)
            if estimates:
                monthly_rows.append({"month": str(month), "method": method, "specification": specification, **estimates})
monthly = pd.DataFrame(monthly_rows)
for coefficient in ["intercept", *SIGNALS]:
    if coefficient not in monthly:
        monthly[coefficient] = np.nan
monthly = monthly[["month", "method", "specification", "nobs", "intercept", *SIGNALS]]
OUTPUT_DIR.mkdir(exist_ok=True)
monthly.to_csv(OUTPUT_DIR / "q3d_monthly_coefficients.csv", index=False)
# Retain the original root-level export for backward compatibility.
monthly.to_csv("q3d_monthly_coefficients.csv", index=False)

# Fama--MacBeth estimates and both requested inference methods.
summary_rows = []
for method in ["OLS", "WLS"]:
    for specification, predictors in SPECIFICATIONS.items():
        subset = monthly.loc[(monthly["method"] == method) & (monthly["specification"] == specification)]
        for coefficient in ["intercept", *predictors]:
            statistics = summarize_coefficients(subset[coefficient])
            summary_rows.append({
                "method": method,
                "specification": specification,
                "coefficient": coefficient,
                **statistics,
                "mean_cross_section_n": subset["nobs"].mean(),
            })
summary = pd.DataFrame(summary_rows)
summary.to_csv(OUTPUT_DIR / "q3d_fama_macbeth_summary.csv", index=False)
# Retain the original root-level export for backward compatibility.
summary.to_csv("q3d_fama_macbeth_summary.csv", index=False)
write_latex_table(summary, "conventional_t", OUTPUT_DIR / "Q3d_FM_Conventional.tex")
write_latex_table(summary, "nw_t", OUTPUT_DIR / "Q3d_FM_NeweyWest.tex")

print(f"Eligible signal-return observations: {panel['next_excess_return'].notna().sum():,}")
print(f"Regression months: {monthly['month'].nunique()}")
print(summary.to_string(index=False, formatters={"estimate": "{:.6f}".format, "conventional_t": "{:.3f}".format, "nw_t": "{:.3f}".format}))
