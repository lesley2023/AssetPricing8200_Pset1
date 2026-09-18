"""Question 2(b): predictive regression with five standard-error methods."""

import numpy as np
import pandas as pd
import statsmodels.api as sm


def hac_covariance(model, nlags, kernel):
    """HAC covariance using the assignment's 1/(T-lag) normalization."""
    X = np.asarray(model.model.exog)
    residuals = np.asarray(model.resid)
    scores = X * residuals[:, None]
    T = len(residuals)

    omega = scores.T @ scores / T
    for lag in range(1, nlags + 1):
        gamma_lag = scores[lag:].T @ scores[:-lag] / (T - lag)
        if kernel == "bartlett":
            weight = 1 - lag / (nlags + 1)
        elif kernel == "uniform":
            weight = 1.0
        else:
            raise ValueError("kernel must be 'bartlett' or 'uniform'")
        omega += weight * (gamma_lag + gamma_lag.T)

    Q_inv = np.linalg.inv(X.T @ X / T)
    return Q_inv @ omega @ Q_inv / T


def nw94_bandwidth(model):
    """Newey-West (1994) plug-in bandwidth for the Bartlett kernel.

    This is the non-prewhitened procedure. Following Newey and West's
    recommended implementation, the intercept estimating equation receives
    zero weight when selecting the bandwidth.
    """
    residuals = np.asarray(model.resid)
    scores = model.model.exog * residuals[:, None]
    weighted_score = scores[:, 1]  # slope score; omit the intercept score
    T = len(weighted_score)

    # Pilot lag truncation for the Bartlett kernel.
    pilot_lag = int(np.floor(4 * (T / 100) ** (2 / 9)))

    # Biased sample autocovariances use T in the denominator, as in NW (1994).
    gamma = np.array(
        [
            np.dot(weighted_score[: T - lag], weighted_score[lag:]) / T
            for lag in range(pilot_lag + 1)
        ]
    )
    s0 = gamma[0] + 2 * gamma[1:].sum()
    s1 = 2 * np.dot(np.arange(1, pilot_lag + 1), gamma[1:])

    bandwidth = 1.1447 * (((s1 / s0) ** 2) * T) ** (1 / 3)
    selected_lag = int(np.floor(bandwidth))
    return bandwidth, selected_lag, pilot_lag


# Read and inspect the monthly observations of annual variables.
df = pd.read_csv("EQ Dataset.csv")
print(df.head())

df["date"] = pd.to_datetime(
    {"year": df["YEAR"], "month": df["MONTH"], "day": 1}
)
df = df.sort_values("date").reset_index(drop=True)

print("\nMissing values by column:")
print(df.isna().sum())

expected_dates = pd.date_range(df["date"].iloc[0], df["date"].iloc[-1], freq="MS")
if not df["date"].equals(pd.Series(expected_dates, name="date")):
    raise ValueError("The dataset is not a complete sequence of monthly observations.")

# Construct simple annual returns and the current dividend-price ratio.
df["Re"] = np.exp(df["re"])
df["Rf"] = np.exp(df["rf"])
df["xRe"] = df["Re"] - df["Rf"]
df["DP"] = np.exp(df["dp"])

# Pair current DP_t with the annual excess return exactly 12 rows ahead.
df["xRe_t_plus_12"] = df["xRe"].shift(-12)
reg = df[["date", "DP", "xRe_t_plus_12"]].dropna().copy()
X = sm.add_constant(reg["DP"])
model = sm.OLS(reg["xRe_t_plus_12"], X).fit()

print(f"\nNumber of regression observations: {int(model.nobs)}")
print("Predictor: current DP_t")
print("Dependent variable: xRe exactly 12 monthly rows ahead")
print(reg.head())

# The coefficient estimate is common to all five covariance estimators.
b_hat = model.params["DP"]

ols_se = model.bse["DP"]
white_se = model.get_robustcov_results(cov_type="HC0").bse[1]
nw11_cov = hac_covariance(model, nlags=11, kernel="bartlett")
nw11_se = np.sqrt(nw11_cov[1, 1])

# Hansen-Hodrick uses equal weights rather than Bartlett weights.
hh11_cov = hac_covariance(model, nlags=11, kernel="uniform")
hh11_se = np.sqrt(hh11_cov[1, 1])

# Newey-West (1994) automatic Bartlett bandwidth and associated integer lag.
nw94_bw, nw94_lag, pilot_lag = nw94_bandwidth(model)
nw94_cov = hac_covariance(model, nlags=nw94_lag, kernel="bartlett")
nw94_se = np.sqrt(nw94_cov[1, 1])

rows = [
    ("Baseline OLS", ols_se, "0"),
    ("White (HC0)", white_se, "0"),
    ("Newey-West (1987)", nw11_se, "11"),
    ("Hansen-Hodrick (1980)", hh11_se, "11"),
    (
        "Newey-West (1994), automatic",
        nw94_se,
        f"{nw94_bw:.3f} (L={nw94_lag}; pilot={pilot_lag})",
    ),
]

results = pd.DataFrame(
    [
        {
            "Method": method,
            "b_hat": b_hat,
            "SE_b": se,
            "t_b": b_hat / se,
            "Lags/bandwidth": lags,
        }
        for method, se, lags in rows
    ]
)

print("\nQ2(b) results:")
print(results.to_string(index=False, float_format=lambda value: f"{value:.6f}"))
