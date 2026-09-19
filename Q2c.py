"""Question 2(c): Amihud-Hurvich reduced-bias predictive regression."""

import numpy as np
import pandas as pd
import statsmodels.api as sm


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

# Construct the simple annual excess return and dividend-price ratio.
df["xRe"] = np.exp(df["re"]) - np.exp(df["rf"])
df["DP"] = np.exp(df["dp"])

# Align current DP with DP and xRe exactly 12 monthly rows ahead.
df["DP_t_plus_12"] = df["DP"].shift(-12)
df["xRe_t_plus_12"] = df["xRe"].shift(-12)
reg = df[["date", "DP", "DP_t_plus_12", "xRe_t_plus_12"]].dropna().copy()

# First-stage persistence regression: DP_(tau+12) on DP_tau.
X_persistence = sm.add_constant(reg["DP"])
persistence = sm.OLS(reg["DP_t_plus_12"], X_persistence).fit()
theta_hat = persistence.params["const"]
phi_hat = persistence.params["DP"]

# Count the distinct calendar years represented in the dataset.
T_years = df["YEAR"].nunique()
phi_corrected = (
    phi_hat
    + (1 / T_years) * (1 + 3 * phi_hat)
    + (3 / T_years**2) * (1 + 3 * phi_hat)
)

# Bias-corrected persistence residual.
reg["u_corrected"] = reg["DP_t_plus_12"] - (
    theta_hat + phi_corrected * reg["DP"]
)

# Final Amihud-Hurvich predictive regression.
X_ah = sm.add_constant(reg[["DP", "u_corrected"]])
ah_model = sm.OLS(reg["xRe_t_plus_12"], X_ah).fit()
b_ah = ah_model.params["DP"]
b_u = ah_model.params["u_corrected"]

# Standard OLS predictive regression on the identical aligned sample.
X_ols = sm.add_constant(reg["DP"])
ols_model = sm.OLS(reg["xRe_t_plus_12"], X_ols).fit()
b_ols = ols_model.params["DP"]

results = pd.DataFrame(
    {
        "Quantity": [
            "theta_hat",
            "phi_hat",
            "T_years",
            "phi_corrected",
            "b_AH",
            "b_u",
            "b_OLS",
            "b_AH_minus_b_OLS",
            "Observations",
        ],
        "Estimate": [
            theta_hat,
            phi_hat,
            T_years,
            phi_corrected,
            b_ah,
            b_u,
            b_ols,
            b_ah - b_ols,
            int(len(reg)),
        ],
    }
)

print(
    f"\nT = number of distinct YEAR values from {df['YEAR'].min()} "
    f"through {df['YEAR'].max()} = {T_years}"
)
print(f"Aligned sample: {reg['date'].iloc[0].date()} through {reg['date'].iloc[-1].date()}")
print(f"First future date: {df['date'].shift(-12).loc[reg.index[0]].date()}")
print("\nQ2(c) results:")
print(results.to_string(index=False, float_format=lambda value: f"{value:.6f}"))
