"""Question 4(c): forward-rate bond return-predictability regressions."""

import numpy as np
import pandas as pd
import statsmodels.api as sm


def newey_west_covariance(model, nlags):
    """Bartlett-weight HAC covariance using the assignment's normalization."""
    X = np.asarray(model.model.exog)
    residuals = np.asarray(model.resid)
    scores = X * residuals[:, None]
    T = len(residuals)

    spectral_density = scores.T @ scores / T
    for lag in range(1, nlags + 1):
        omega_lag = scores[lag:].T @ scores[:-lag] / (T - lag)
        weight = 1 - lag / (nlags + 1)
        spectral_density += weight * (omega_lag + omega_lag.T)

    Q_inv = np.linalg.inv(X.T @ X / T)
    return Q_inv @ spectral_density @ Q_inv / T


def nw94_bandwidth(model):
    """Select the Newey-West (1994) automatic Bartlett bandwidth."""
    residuals = np.asarray(model.resid)
    scores = np.asarray(model.model.exog) * residuals[:, None]
    slope_score = scores[:, 1]  # Exclude the intercept estimating equation.
    T = len(slope_score)

    pilot_lag = int(np.floor(4 * (T / 100) ** (2 / 9)))
    gamma = np.array(
        [
            np.dot(slope_score[: T - lag], slope_score[lag:]) / T
            for lag in range(pilot_lag + 1)
        ]
    )
    s0 = gamma[0] + 2 * gamma[1:].sum()
    s1 = 2 * np.dot(np.arange(1, pilot_lag + 1), gamma[1:])
    bandwidth = 1.1447 * (((s1 / s0) ** 2) * T) ** (1 / 3)
    selected_lag = int(np.floor(bandwidth))
    return bandwidth, selected_lag


# Load and reshape the nominal Fama-Bliss yields for maturities 1--5.
df = pd.read_csv("Bond Dataset.csv")
label_pattern = r"^Fama Bliss Discount Bonds - ([1-5])-Year \(Nominal\)$"
bond = df[df["TTERMLBL"].str.match(label_pattern, na=False)].copy()
bond["date"] = pd.to_datetime(bond["MCALDT"]).dt.to_period("M").dt.to_timestamp()
bond["H"] = bond["TTERMLBL"].str.extract(label_pattern, expand=False).astype(int)
bond["Y"] = bond["TMYTM"] / 100

Y = bond.pivot(index="date", columns="H", values="Y").sort_index()
Y = Y.reindex(columns=range(1, 6))
y = np.log1p(Y)

# Construct forward rates and 12-month annual returns from Question 4(a).
f = pd.DataFrame(index=y.index, columns=y.columns, dtype=float)
f[1] = y[1]
r = pd.DataFrame(index=y.index, columns=y.columns, dtype=float)
r[1] = y[1].shift(12)
for H in range(2, 6):
    f[H] = H * y[H] - (H - 1) * y[H - 1]
    r[H] = H * y[H].shift(12) - (H - 1) * y[H - 1]

xf = f.subtract(f[1], axis=0)
xr = r.subtract(r[1], axis=0)

rows = []
for H in range(2, 6):
    # shift(-12) pairs the forward spread at t with the return ending at t+12.
    regression = pd.DataFrame(
        {"dependent": xr[H].shift(-12), "predictor": xf[H]}
    ).dropna()

    X = sm.add_constant(regression["predictor"])
    model = sm.OLS(regression["dependent"], X).fit()

    # Select L separately for each maturity, then use Bartlett HAC weights.
    bandwidth, selected_lag = nw94_bandwidth(model)
    nw_cov = newey_west_covariance(model, selected_lag)
    slope_se = np.sqrt(nw_cov[1, 1])

    rows.append(
        {
            "H": H,
            "b": model.params["predictor"],
            "NW t-stat": model.params["predictor"] / slope_se,
            "R2 percent": 100 * model.rsquared,
            "N": int(model.nobs),
            "bandwidth": bandwidth,
            "L": selected_lag,
        }
    )

results = pd.DataFrame(rows).set_index("H")
print("Q4(c) regression results:")
print(results.to_string(float_format=lambda value: f"{value:.6f}"))
print("\nSelected Newey-West (1994) lags by maturity:")
for H, row in results.iterrows():
    print(f"H={H}: bandwidth={row['bandwidth']:.4f}, L={int(row['L'])}")
