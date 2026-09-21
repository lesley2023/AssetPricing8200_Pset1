"""Question 4(d): construct and plot the Cochrane-Piazzesi factor."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm


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

# Construct the five log forward rates and annual excess log returns.
f = pd.DataFrame(index=y.index, columns=y.columns, dtype=float)
f[1] = y[1]
r = pd.DataFrame(index=y.index, columns=y.columns, dtype=float)
r[1] = y[1].shift(12)
for H in range(2, 6):
    f[H] = H * y[H] - (H - 1) * y[H - 1]
    r[H] = H * y[H].shift(12) - (H - 1) * y[H - 1]
xr = r.subtract(r[1], axis=0)

# Align current forwards at t with the average excess return ending at t+12.
average_future_xr = xr.loc[:, 2:5].mean(axis=1).shift(-12)
regression = f.copy()
regression.columns = [f"f{H}" for H in range(1, 6)]
regression["average_future_xr"] = average_future_xr
regression = regression.dropna()

X = sm.add_constant(regression[[f"f{H}" for H in range(1, 6)]])
model = sm.OLS(regression["average_future_xr"], X).fit()

print("Q4(d) OLS estimates:")
for name, value in model.params.items():
    print(f"{name}: {value:.8f}")
print(f"R-squared: {model.rsquared:.8f}")
print(f"Number of observations: {int(model.nobs)}")
print(f"First starting month: {regression.index.min():%Y-%m}")
print(f"Last starting month: {regression.index.max():%Y-%m}")

# The CP factor excludes the estimated intercept and remains in decimal log units.
slope_names = [f"f{H}" for H in range(1, 6)]
cp = f.mul(model.params[slope_names].to_numpy(), axis=1).sum(axis=1, min_count=5)
cp_data = cp.rename("cp_t").reset_index()
cp_data.to_csv("q4d_cp_factor.csv", index=False)

# Merge the factor with the monthly NBER recession indicator.
recession = pd.read_csv("Recession.csv")
recession["date"] = (
    pd.to_datetime(recession["observation_date"]).dt.to_period("M").dt.to_timestamp()
)
plot_data = cp_data.merge(recession[["date", "USREC"]], on="date", how="left")
if plot_data["USREC"].isna().any():
    raise ValueError("Recession.csv does not cover every CP-factor month.")

# Combine consecutive recession months into continuous shaded intervals.
recession_months = plot_data.loc[plot_data["USREC"].eq(1), "date"]
groups = recession_months.diff().ne(pd.offsets.MonthBegin(1)).cumsum()
recession_intervals = recession_months.groupby(groups).agg(["min", "max"])

fig, ax = plt.subplots(figsize=(11, 5.5))
ax.plot(
    plot_data["date"],
    100 * plot_data["cp_t"],
    color="#1f4e79",
    linewidth=1.2,
    label="CP factor",
)
ax.axhline(0, color="black", linewidth=0.8)

for i, interval in recession_intervals.iterrows():
    ax.axvspan(
        interval["min"],
        interval["max"] + pd.offsets.MonthBegin(1),
        color="lightgray",
        alpha=0.65,
        linewidth=0,
        label="NBER recession" if i == recession_intervals.index[0] else None,
    )

ax.set_title("Cochrane-Piazzesi Factor")
ax.set_xlabel("Date")
ax.set_ylabel("cp_t (%)")
ax.legend(frameon=False, loc="best")
ax.grid(axis="y", color="0.88", linewidth=0.6)
ax.margins(x=0)
fig.tight_layout()
fig.savefig("figures/q4d_cp_factor.png", dpi=300, bbox_inches="tight")
plt.close(fig)
