"""Question 3(e): portfolio-panel regressions with Driscoll--Kraay inference."""

from __future__ import annotations

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


def assign_deciles(values: pd.Series, reference: pd.Series | None = None) -> pd.Series:
    reference_values = (values if reference is None else reference).dropna().to_numpy(dtype=float)
    result = pd.Series(np.nan, index=values.index)
    valid = values.notna()
    if reference_values.size < 10 or not valid.any():
        return result
    cutoffs = np.quantile(reference_values, np.arange(0.1, 1.0, 0.1))
    result.loc[valid] = np.searchsorted(cutoffs, values.loc[valid].to_numpy(dtype=float), side="right") + 1
    return result


def nyse_formation_deciles(group: pd.DataFrame, signal: str) -> pd.Series:
    return assign_deciles(group[signal], group.loc[group["EXCHCD"].eq(1), signal])


def automatic_bandwidth(time_periods: int) -> int:
    """Common default bandwidth for Bartlett-kernel Driscoll--Kraay covariance."""
    return int(np.floor(4.0 * (time_periods / 100.0) ** (2.0 / 9.0)))


def pooled_ols_dk(frame: pd.DataFrame, predictors: list[str]) -> dict:
    columns = [f"Dec_{signal}" for signal in predictors]
    sample = frame.dropna(subset=["excess_return", *columns]).sort_values(["month", "portfolio_id"])
    x = np.column_stack([np.ones(len(sample)), sample[columns].to_numpy(dtype=float)])
    y = sample["excess_return"].to_numpy(dtype=float)
    beta = np.linalg.lstsq(x, y, rcond=None)[0]
    residual = y - np.einsum("ij,j->i", x, beta)

    # Aggregate score vectors within month; this permits unrestricted
    # contemporaneous dependence across the 30 portfolios.
    score_rows = pd.DataFrame(x * residual[:, None])
    score_rows["month"] = sample["month"].astype(str).to_numpy()
    scores = score_rows.groupby("month", sort=True).sum().to_numpy(dtype=float)
    time_periods = scores.shape[0]
    bandwidth = min(automatic_bandwidth(time_periods), time_periods - 1)
    meat = np.einsum("ti,tj->ij", scores, scores)
    for lag in range(1, bandwidth + 1):
        weight = 1.0 - lag / (bandwidth + 1.0)
        gamma = np.einsum("ti,tj->ij", scores[lag:], scores[:-lag])
        meat += weight * (gamma + gamma.T)
    bread = np.linalg.inv(x.T @ x)
    covariance = bread @ meat @ bread
    covariance *= len(sample) / (len(sample) - x.shape[1])
    standard_errors = np.sqrt(np.clip(np.diag(covariance), 0.0, None))
    t_statistics = beta / standard_errors
    names = ["intercept", *predictors]
    return {
        "coefficients": dict(zip(names, beta)),
        "standard_errors": dict(zip(names, standard_errors)),
        "t_statistics": dict(zip(names, t_statistics)),
        "observations": len(sample),
        "months": time_periods,
        "bandwidth": bandwidth,
    }


def significance_stars(t_stat: float) -> str:
    absolute_t = abs(t_stat)
    if absolute_t >= 2.575829:
        return "***"
    if absolute_t >= 1.959964:
        return "**"
    if absolute_t >= 1.644854:
        return "*"
    return ""


def tex_number(value: float, decimals: int) -> str:
    formatted = f"{value:.{decimals}f}"
    return f"${formatted}$" if value < 0 else formatted


def tex_estimate(value: float, t_stat: float) -> str:
    formatted = f"{100.0 * value:.4f}"
    stars = significance_stars(t_stat)
    if value < 0 or stars:
        superscript = rf"^{{{stars}}}" if stars else ""
        return f"${formatted}{superscript}$"
    return formatted


def write_latex_table(summary: pd.DataFrame, destination: Path) -> None:
    lookup = summary.set_index(["weighting", "specification", "coefficient"])

    def cell(weighting: str, specification: int, coefficient: str) -> str:
        if coefficient not in ["intercept", *SPECIFICATIONS[specification]]:
            return ""
        row = lookup.loc[(weighting, specification, coefficient)]
        estimate = tex_estimate(row["estimate"], row["dk_t"])
        t_stat = tex_number(row["dk_t"], 2)
        return rf"\dkcell{{{estimate}}}{{{t_stat}}}"

    lines = [
        r"\begin{table}[!htbp]",
        r"    \centering",
        r"    \caption{Portfolio-panel regressions with Driscoll--Kraay inference}",
        r"    \label{tab:q3e_pooled_ols}",
        r"    \newcommand{\dkcell}[2]{\shortstack{#1\\(#2)}}",
        r"    \resizebox{\textwidth}{!}{%",
        r"    \begin{tabular}{lccccccc}",
        r"        \toprule",
        r"        & (1) & (2) & (3) & (4) & (5) & (6) & (7) \\",
        r"        \midrule",
    ]
    labels = {"intercept": "Intercept", "BM": r"$Dec^{BM}$", "GP": r"$Dec^{GP}$", "Dur": r"$Dec^{Dur}$"}
    for panel, weighting in [("Panel A: Value-weighted portfolios", "VW"), ("Panel B: Equal-weighted portfolios", "EW")]:
        if weighting == "EW":
            lines.append(r"        \midrule")
        lines.append(rf"        \multicolumn{{8}}{{l}}{{\textit{{{panel}}}}} \\")
        for coefficient in ["intercept", "BM", "GP", "Dur"]:
            cells = [cell(weighting, specification, coefficient) for specification in SPECIFICATIONS]
            lines.append(f"        {labels[coefficient]} & " + " & ".join(cells) + r" \\")
        observations = [int(lookup.loc[(weighting, specification, "intercept"), "observations"]) for specification in SPECIFICATIONS]
        lines.append("        Observations & " + " & ".join(map(str, observations)) + r" \\")
    lines.extend([
        r"        \bottomrule",
        r"    \end{tabular}%",
        r"    }",
        r"",
        r"    \vspace{0.5em}",
        r"    \begin{minipage}{0.98\textwidth}",
        r"    \footnotesize",
        r"    \textit{Notes:} Coefficients are monthly percentage points. The panel contains 30 annually rebalanced portfolios formed at June using NYSE breakpoints: ten each for BM, GP, and duration. Stock-level monthly cross-sectional decile assignments are identical in both panels. In Panel A, portfolio returns and $Dec^{BM}$, $Dec^{GP}$, and $Dec^{Dur}$ use month-$\tau$ market-equity weights. In Panel B, portfolio returns and all three portfolio-level decile measures use equal constituent weights (arithmetic averages). Pooled OLS is estimated separately by panel. Driscoll--Kraay $t$-statistics using a Bartlett kernel and automatic bandwidth are reported in parentheses. $^{***}$, $^{**}$, and $^{*}$ denote two-sided significance at the 1\%, 5\%, and 10\% levels, respectively.",
        r"    \end{minipage}",
        r"\end{table}",
        r"\FloatBarrier",
        "",
    ])
    destination.write_text("\n".join(lines), encoding="utf-8")


# Monthly CZ signals and annual June duration signal.
cz = load_cz("BMdec.csv", "BMdec", "BM").merge(
    load_cz("GP.csv", "GP", "GP"), on=["PERMNO", "yyyymm"], how="inner", validate="one_to_one"
)
cz["month"] = pd.PeriodIndex(cz["yyyymm"].astype(str), freq="M")
cz["formation_year"] = np.where(cz["month"].dt.month.ge(6), cz["month"].dt.year, cz["month"].dt.year - 1)
duration = pd.read_csv(DATA_DIR / "Dur Dataset.csv", usecols=["PERMNO", "FF.YEAR", "Dur"])
for column in ["PERMNO", "FF.YEAR", "Dur"]:
    duration[column] = pd.to_numeric(duration[column], errors="coerce")
duration = duration.dropna().rename(columns={"FF.YEAR": "formation_year"})
duration[["PERMNO", "formation_year"]] = duration[["PERMNO", "formation_year"]].astype("int64")
if duration.duplicated(["PERMNO", "formation_year"]).any():
    raise ValueError("Duration file contains duplicate PERMNO-year observations")
signals = cz.merge(duration, on=["PERMNO", "formation_year"], how="inner", validate="many_to_one")

# Construct consecutive next-month returns before screening the formation-month universe.
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
crsp = crsp.loc[eligible, ["PERMNO", "month", "EXCHCD", "ME", "next_return"]].copy()
crsp["yyyymm"] = crsp["month"].dt.year * 100 + crsp["month"].dt.month
panel = crsp.merge(signals[["PERMNO", "yyyymm", *SIGNALS]], on=["PERMNO", "yyyymm"], how="inner")

# Current cross-sectional ranks are common to the VW and EW analyses.
for signal in SIGNALS:
    panel[QUANTILES[signal]] = panel.groupby("month", observed=True)[signal].transform(assign_deciles)

# June NYSE breakpoints determine annual portfolio assignments for July--June returns.
june = panel.loc[panel["month"].dt.month.eq(6), ["PERMNO", "month", "EXCHCD", *SIGNALS]].copy()
june["formation_year"] = june["month"].dt.year
formation_rows = []
for signal in SIGNALS:
    assigned = june[["PERMNO", "formation_year", "month", "EXCHCD", signal]].copy()
    assigned["portfolio_decile"] = assigned.groupby("formation_year", group_keys=False, observed=True).apply(
        nyse_formation_deciles, signal=signal, include_groups=False
    )
    assigned["formed_on"] = signal
    formation_rows.append(assigned[["PERMNO", "formation_year", "formed_on", "portfolio_decile"]])
formation = pd.concat(formation_rows, ignore_index=True).dropna(subset=["portfolio_decile"])
formation["portfolio_decile"] = formation["portfolio_decile"].astype("int8")

holdings = panel.copy()
holdings["formation_year"] = np.where(
    holdings["month"].dt.month.ge(6), holdings["month"].dt.year, holdings["month"].dt.year - 1
)
holdings = holdings.merge(formation, on=["PERMNO", "formation_year"], how="inner", validate="many_to_many")
holdings = holdings.dropna(subset=["next_return", "ME", *QUANTILES.values()])
holdings = holdings.loc[holdings["ME"].gt(0)].copy()
holdings["portfolio_id"] = holdings["formed_on"] + holdings["portfolio_decile"].astype(str)

# Risk-free return belongs to the next-month portfolio return.
ff = pd.read_csv(DATA_DIR / "fama_french.csv", skiprows=3)
ff = ff.rename(columns={ff.columns[0]: "yyyymm"})
ff["yyyymm"] = pd.to_numeric(ff["yyyymm"], errors="coerce")
ff["RF"] = pd.to_numeric(ff["RF"], errors="coerce") / 100.0
ff = ff.loc[ff["yyyymm"].between(100000, 999999), ["yyyymm", "RF"]]
ff["return_month"] = pd.PeriodIndex(ff["yyyymm"].astype(int).astype(str), freq="M")

portfolio_rows = []
group_keys = ["month", "formed_on", "portfolio_decile", "portfolio_id"]
for weighting in ["VW", "EW"]:
    work = holdings.copy()
    if weighting == "VW":
        work["weighted_return"] = work["next_return"] * work["ME"]
        for signal in SIGNALS:
            work[f"weighted_Q_{signal}"] = work[QUANTILES[signal]] * work["ME"]
        returns = work.groupby(group_keys, observed=True).agg(
            numerator=("weighted_return", "sum"), denominator=("ME", "sum"), firms=("PERMNO", "size")
        )
        returns["portfolio_return"] = returns["numerator"] / returns["denominator"]
        weighted_characteristics = work.groupby(group_keys, observed=True).agg(
            weighted_Dec_BM=("weighted_Q_BM", "sum"),
            weighted_Dec_GP=("weighted_Q_GP", "sum"),
            weighted_Dec_Dur=("weighted_Q_Dur", "sum"),
        )
        characteristics = pd.DataFrame(index=weighted_characteristics.index)
        for signal in SIGNALS:
            characteristics[f"Dec_{signal}"] = (
                weighted_characteristics[f"weighted_Dec_{signal}"] / returns["denominator"]
            )
    else:
        returns = work.groupby(group_keys, observed=True).agg(
            portfolio_return=("next_return", "mean"), firms=("PERMNO", "size")
        )
        characteristics = work.groupby(group_keys, observed=True).agg(
            Dec_BM=("Q_BM", "mean"), Dec_GP=("Q_GP", "mean"), Dec_Dur=("Q_Dur", "mean")
        )
    portfolios = returns[["portfolio_return", "firms"]].join(characteristics).reset_index()
    portfolios["weighting"] = weighting
    portfolio_rows.append(portfolios)

portfolio_panel = pd.concat(portfolio_rows, ignore_index=True)
portfolio_panel["return_month"] = portfolio_panel["month"] + 1
portfolio_panel = portfolio_panel.merge(ff[["return_month", "RF"]], on="return_month", how="inner", validate="many_to_one")
portfolio_panel["excess_return"] = portfolio_panel["portfolio_return"] - portfolio_panel["RF"]
portfolio_panel = portfolio_panel.sort_values(["weighting", "month", "formed_on", "portfolio_decile"])

OUTPUT_DIR.mkdir(exist_ok=True)
portfolio_panel.to_csv(OUTPUT_DIR / "q3e_portfolio_month_panel.csv", index=False)

summary_rows = []
for weighting in ["VW", "EW"]:
    weighting_panel = portfolio_panel.loc[portfolio_panel["weighting"].eq(weighting)]
    for specification, predictors in SPECIFICATIONS.items():
        specification_panel = weighting_panel.loc[weighting_panel["formed_on"].isin(predictors)]
        result = pooled_ols_dk(specification_panel, predictors)
        for coefficient in ["intercept", *predictors]:
            summary_rows.append({
                "weighting": weighting,
                "specification": specification,
                "coefficient": coefficient,
                "estimate": result["coefficients"][coefficient],
                "dk_se": result["standard_errors"][coefficient],
                "dk_t": result["t_statistics"][coefficient],
                "observations": result["observations"],
                "months": result["months"],
                "bandwidth": result["bandwidth"],
            })
summary = pd.DataFrame(summary_rows)
summary.to_csv(OUTPUT_DIR / "q3e_pooled_ols_summary.csv", index=False)
write_latex_table(summary, OUTPUT_DIR / "Q3e_Pooled_OLS.tex")

print(f"Portfolio-month rows: {len(portfolio_panel):,}")
print(f"Months: {portfolio_panel['month'].nunique()}")
print(summary.to_string(index=False, formatters={"estimate": "{:.6f}".format, "dk_t": "{:.3f}".format}))
