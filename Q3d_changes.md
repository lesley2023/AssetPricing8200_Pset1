# Question 3(d) changes

- Added `Q3d.py` to merge the monthly BMCZ and GPCZ signals with the annual June equity-duration signal and the eligible CRSP universe.
- Assigned monthly cross-sectional deciles for BM, GP, and duration and aligned month-t signals and market equity with month-t+1 excess returns.
- Estimated all seven requested specifications using monthly OLS and market-equity-weighted WLS cross-sectional regressions.
- Calculated Fama--MacBeth coefficient averages, conventional standard errors and t-statistics, and Newey--West standard errors and t-statistics with automatically selected lag lengths.
- Saved the monthly coefficients and final summary as CSV files in `output/`.
- Generated separate conventional and Newey--West LaTeX table fragments in `output/`; `solution.tex` includes only the conventional Fama--MacBeth table requested for the main answer.
- Added superscript significance stars using two-sided 1%, 5%, and 10% critical values, calculated separately from conventional and Newey--West t-statistics in their respective tables.
