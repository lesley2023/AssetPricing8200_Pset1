# Question 3(b) changes

- Added `Q3b.py` to construct annual book equity from Compustat using the requested stockholders' equity, deferred-tax, and preferred-stock hierarchy.
- Used the calendar year of the actual Compustat fiscal year-end (`datadate`), rather than the `fyear` label, to match fiscal-year data ending in calendar year t-1 to the June t portfolio-formation date.
- Required two earlier Compustat fiscal-year records, positive book equity, and a valid CRSP--Compustat link at the June portfolio-formation date.
- Constructed December market equity as absolute price times shares outstanding and calculated book-to-market using the compatible Compustat/CRSP units.
- Assigned each June book-to-market signal through the following May and applied the requested share-code, exchange, SIC-industry, and June 1963 start-date restrictions.
- Merged the constructed signal with `BMdec.csv`, used the revised level comparison `BM_CZ = BMdec`, and estimated the monthly cross-sectional regressions.
- Saved the monthly regression output to `q3b_monthly_regressions.csv` and generated intercept, slope, and R-squared plots in `figures/`.
- Added only the three requested figures to Question 3(b) in `solution.tex`, without explanatory answer text.
