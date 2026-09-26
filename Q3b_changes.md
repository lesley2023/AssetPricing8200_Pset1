# Question 3(b) changes

- Added `Q3b.py` to construct annual book equity from Compustat using the requested stockholders' equity, deferred-tax, and preferred-stock hierarchy.
- Used the Compustat `fyear` label to match fiscal-year t-1 accounting data to the June t portfolio-formation date; `datadate` is retained to choose the latest record within a duplicated company-fiscal-year label.
- Separated the company accounting history from the repeated CRSP link rows, then constructed a date-specific June crosswalk using valid `LC`/`LU` links and primary/consolidated `P`/`C` link status. The script raises an error rather than choosing arbitrarily if multiple primary PERMNOs remain for a company-year.
- Required two earlier Compustat fiscal-year records, positive book equity, and a valid CRSP--Compustat link at the June portfolio-formation date.
- Constructed December market equity as absolute price times shares outstanding and calculated book-to-market using the compatible Compustat/CRSP units.
- Assigned each June book-to-market signal through the following May and applied the requested share-code, exchange, SIC-industry, and June 1963 start-date restrictions.
- Merged the constructed signal with `BMdec.csv`, used the revised level comparison `BM_CZ = BMdec`, and estimated the monthly cross-sectional regressions.
- Saved the monthly regression output to `q3b_monthly_regressions.csv` and generated intercept, slope, and R-squared plots in `figures/`.
- Added only the three requested figures to Question 3(b) in `solution.tex`, without explanatory answer text.
- Added `Q3b_winsorized.py` as a separate robustness script. It caps both BM measures at their monthly 1st and 99th percentiles, saves a separate regression CSV, and generates three clearly labeled robustness figures motivated by the high leverage of PERMNO 18558.
