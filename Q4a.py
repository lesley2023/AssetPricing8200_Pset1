"""Question 4(a): average bond excess yields, forward rates, and returns."""

import numpy as np
import pandas as pd


# Read the bond data and inspect its structure and available series.
df = pd.read_csv("Bond Dataset.csv")
print(df.head())
print("\nUnique TTERMLBL values:")
print(df["TTERMLBL"].dropna().unique())

# Retain the nominal Fama-Bliss discount-bond yields for maturities 1--5.
label_pattern = r"^Fama Bliss Discount Bonds - ([1-5])-Year \(Nominal\)$"
bond = df[df["TTERMLBL"].str.match(label_pattern, na=False)].copy()
bond["date"] = pd.to_datetime(bond["MCALDT"]).dt.to_period("M").dt.to_timestamp()
bond["H"] = bond["TTERMLBL"].str.extract(label_pattern, expand=False).astype(int)
bond = bond.sort_values(["date", "H"])

# Convert percentage yields to decimals and reshape to one row per month.
bond["Y"] = bond["TMYTM"] / 100
Y = bond.pivot(index="date", columns="H", values="Y").sort_index()
Y = Y.reindex(columns=range(1, 6))

print("\nMissing decimal yields by maturity:")
print(Y.isna().sum())

# Construct log yields and same-month log forward rates.
y = np.log1p(Y)
f = pd.DataFrame(index=y.index, columns=y.columns, dtype=float)
f[1] = y[1]
for H in range(2, 6):
    f[H] = H * y[H] - (H - 1) * y[H - 1]

# Construct annual log returns using yields 12 months apart.
r = pd.DataFrame(index=y.index, columns=y.columns, dtype=float)
r[1] = y[1].shift(12)
for H in range(2, 6):
    r[H] = H * y[H].shift(12) - (H - 1) * y[H - 1]

# Subtract the one-year series and average each column using available values.
xy = y.subtract(y[1], axis=0)
xf = f.subtract(f[1], axis=0)
xr = r.subtract(r[1], axis=0)

# Multiply the averages by 100 for reporting in percentage terms.
results = 100 * pd.DataFrame(
    {
        "Average xy": xy.loc[:, 2:5].mean(skipna=True),
        "Average xf": xf.loc[:, 2:5].mean(skipna=True),
        "Average xr": xr.loc[:, 2:5].mean(skipna=True),
    }
)
results.index.name = "H"

print("\nQ4(a) time-series averages (percent):")
print(results.to_string(float_format=lambda value: f"{value:.6f}"))
print("\nAvailable observations used in each average:")
print(
    pd.DataFrame(
        {
            "xy": xy.loc[:, 2:5].count(),
            "xf": xf.loc[:, 2:5].count(),
            "xr": xr.loc[:, 2:5].count(),
        }
    ).to_string()
)
