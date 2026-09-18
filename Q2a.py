"""Question 2(a): long-horizon equity-return predictability regressions."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm


# Read the monthly data and inspect its structure.
df = pd.read_csv("EQ Dataset.csv")
print(df.head())

# Build a monthly date and place the observations in chronological order.
df["date"] = pd.to_datetime(
    {"year": df["YEAR"], "month": df["MONTH"], "day": 1}
)
df = df.sort_values("date").reset_index(drop=True)

# Check data completeness and verify that the monthly sequence has no gaps.
print("\nMissing values by column:")
print(df.isna().sum())
expected_dates = pd.date_range(df["date"].iloc[0], df["date"].iloc[-1], freq="MS")
if not df["date"].equals(pd.Series(expected_dates, name="date")):
    raise ValueError("The dataset is not a complete sequence of monthly observations.")

# Convert log annual returns and the log dividend-price ratio to simple values.
df["Re"] = np.exp(df["re"])
df["Rf"] = np.exp(df["rf"])
df["xRe"] = df["Re"] - df["Rf"]
df["DP"] = np.exp(df["dp"])

results = []
for H in range(1, 16):
    # Use exactly the annual observations t+12, t+24, ..., t+12H.
    future_returns = pd.concat(
        [df["xRe"].shift(-12 * h) for h in range(1, H + 1)], axis=1
    )

    # Requiring a complete row ensures that no incomplete horizon is averaged.
    complete = future_returns.notna().all(axis=1) & df["DP"].notna()
    y = future_returns.loc[complete].mean(axis=1)
    X = sm.add_constant(df.loc[complete, "DP"])
    model = sm.OLS(y, X).fit()

    results.append(
        {"H": H, "adjusted_R2": model.rsquared_adj, "nobs": int(model.nobs)}
    )

results = pd.DataFrame(results)
print("\nRegression results:")
print(results.to_string(index=False))

# Plot adjusted R-squared against the forecast horizon.
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(results["H"], results["adjusted_R2"], marker="o", linewidth=2)
ax.set_xticks(range(1, 16))
ax.set_xlabel("Horizon H (years)")
ax.set_ylabel(r"Adjusted $R^2$")
ax.set_title("Long-Horizon Excess-Return Predictability")
ax.grid(True, alpha=0.3)

# Label each point with its adjusted R-squared value.
for H, adjusted_r2 in zip(results["H"], results["adjusted_R2"]):
    ax.annotate(
        f"{adjusted_r2:.3f}",
        (H, adjusted_r2),
        xytext=(0, 8),
        textcoords="offset points",
        ha="center",
        fontsize=8,
    )

ax.set_ylim(top=0.48)
fig.tight_layout()
fig.savefig("figures/q2a_adjusted_r2.png", dpi=300, bbox_inches="tight")
plt.close(fig)
