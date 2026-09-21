"""Question 4(b): bond return-predictability regressions."""

import numpy as np
import pandas as pd
import statsmodels.api as sm


def hansen_hodrick_covariance(model, nlags):
    """Uniform-weight HAC covariance using the assignment's normalization."""
    X = np.asarray(model.model.exog)
    residuals = np.asarray(model.resid)
    scores = X * residuals[:, None]
    T = len(residuals)

    # Hansen-Hodrick assigns weight one to every autocovariance through L.
    spectral_density = scores.T @ scores / T
    for lag in range(1, nlags + 1):
        omega_lag = scores[lag:].T @ scores[:-lag] / (T - lag)
        spectral_density += omega_lag + omega_lag.T

    Q_inv = np.linalg.inv(X.T @ X / T)
    return Q_inv @ spectral_density @ Q_inv / T


# Load the nominal Fama-Bliss discount-bond yields for maturities 1--5.
df = pd.read_csv("Bond Dataset.csv")
label_pattern = r"^Fama Bliss Discount Bonds - ([1-5])-Year \(Nominal\)$"
bond = df[df["TTERMLBL"].str.match(label_pattern, na=False)].copy()
bond["date"] = pd.to_datetime(bond["MCALDT"]).dt.to_period("M").dt.to_timestamp()
bond["H"] = bond["TTERMLBL"].str.extract(label_pattern, expand=False).astype(int)
bond["Y"] = bond["TMYTM"] / 100

Y = bond.pivot(index="date", columns="H", values="Y").sort_index()
Y = Y.reindex(columns=range(1, 6))
y = np.log1p(Y)

# Annual returns use the yield observed 12 months earlier.
r = pd.DataFrame(index=y.index, columns=y.columns, dtype=float)
r[1] = y[1].shift(12)
for H in range(2, 6):
    r[H] = H * y[H].shift(12) - (H - 1) * y[H - 1]

xy = y.subtract(y[1], axis=0)
xr = r.subtract(r[1], axis=0)

# First construct every maturity's valid regression rows.
regressions = {}
for H in range(2, 6):
    # At t+12h, the held bond's maturity is H-h+1. Include all H terms
    # in the stated hold-to-maturity sum, including the final H=1 term.
    hold_to_maturity = pd.Series(0.0, index=y.index)
    for h in range(1, H + 1):
        declining_maturity = H - h + 1
        hold_to_maturity += xr[declining_maturity].shift(-12 * h)

    regressions[H] = pd.DataFrame(
        {"dependent": hold_to_maturity / H, "predictor": xy[H]}
    ).dropna()

# Restrict all regressions to starting months valid for every maturity.
common_index = regressions[2].index
for H in range(3, 6):
    common_index = common_index.intersection(regressions[H].index)

print(
    f"Common sample: {common_index.min():%Y-%m} to "
    f"{common_index.max():%Y-%m} ({len(common_index)} observations)"
)

rows = []
for H in range(2, 6):
    regression = regressions[H].loc[common_index]
    X = sm.add_constant(regression["predictor"])
    model = sm.OLS(regression["dependent"], X).fit()

    # The H-year holding period implies 12H-1 monthly Hansen-Hodrick lags.
    nlags = 12 * H - 1
    hh_cov = hansen_hodrick_covariance(model, nlags)
    slope_se = np.sqrt(hh_cov[1, 1])

    rows.append(
        {
            "H": H,
            "b": model.params["predictor"],
            "HH t-stat": model.params["predictor"] / slope_se,
            "R2 percent": 100 * model.rsquared,
            "N": int(model.nobs),
            "HH lags": nlags,
        }
    )

results = pd.DataFrame(rows).set_index("H")
print("Q4(b) regression results:")
print(results.to_string(float_format=lambda value: f"{value:.6f}"))
