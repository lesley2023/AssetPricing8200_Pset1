# Question 3(e) changes

- Added `Q3e.py` to construct annually rebalanced BM, GP, and duration decile portfolios using June NYSE breakpoints.
- Calculated value-weighted and equal-weighted next-month portfolio excess returns and the average BM, GP, and duration decile ranks of portfolio constituents.
- Matched each portfolio-level decile measure to its return weighting: month-$\tau$ market-equity weights for the value-weighted panel and simple constituent averages for the equal-weighted panel.
- Estimated all seven pooled portfolio-panel specifications separately for value-weighted and equal-weighted portfolios using Driscoll--Kraay standard errors.
- Added inference-specific significance stars and saved the portfolio-month panel, regression summary, and generated LaTeX table in `output/`.
- Inserted only the generated two-panel Q3(e) table into `solution.tex`, without explanatory answer prose.
