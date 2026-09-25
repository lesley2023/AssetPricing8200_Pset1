# Question 3(a) implementation notes

- Created `Q3a.py` from the instructions in `Q3a_prompt`.
- Constructed each stock's end-of-month momentum signal by compounding its 12 monthly CRSP returns from months $\tau-12$ through $\tau-1$.
- Required all 12 returns to be numeric and the observations to be consecutive calendar months.
- Restricted the signal-month sample to June 1963 onward; share codes 10 or 11; exchange codes 1, 2, or 3; and excluded utilities (SIC 4900--4949) and financials (SIC 6000--6999).
- Merged the filtered CRSP observations with `Q3_Datasets/Mom12m.csv` by `permno` and `yyyymm`, defining `MOMCZ` as `Mom12m`.
- Estimated a separate monthly cross-sectional OLS regression of `MOMCZ` on a constant and `MOM`.
- Saved the monthly intercept, slope, $R^2$, and cross-sectional observation count to `q3a_monthly_regressions.csv`.
- Generated `figures/q3a_intercepts.png`, `figures/q3a_slopes.png`, and `figures/q3a_r2.png`.
- Replaced the Question 3 placeholder in `solution.tex` with only the three requested figures and no explanatory answer text.
- Rebuilt `solution.pdf` and visually checked the pages containing the three figures.
