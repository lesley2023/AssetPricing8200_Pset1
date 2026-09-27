1. In this task, work with the time index \tau = 1,2,...,\Tau, representing months. Use the following three signals:
   1) Q3_Datasets/BMdec.csv: define BMCZ=BMdec.
   2) Q3_Datasets/GP.csv: define GPCZ=GP.
   3) Q3_Datasets/Dur Dataset.csv: use the equity duration variable Dur. The column PERMNO is the stock identifier, FF.YEAR is the year identifier, and Dur contains the respective equity duration. Merge the CZ Dataset with the Dur Dataset using the corresponding stock and year identifiers. The timing of Dur matches the timing of the BM variable: it is calculated at the end of June of year (t), using market equity from December of year (t-1) and accounting information from the fiscal year ending in calendar year (t-1).

2. Use "Q3_Datasets/CRSP_monthly.csv" for stock returns and market equity. Focus on the period from June of 1963 to the recent date. Restrict the analysis to common stocks of firms incorporated in the United States (CRSP shrcd = 10 or 11) trading on NYSE, Amex, or Nasdaq (CRSP exchcd = 1,2 or 3), and exclude utilities (4900 ≤SIC ≤4949) and financials (6000 ≤SIC ≤6999). Calculate monthly market equity using (ME=|PRC|\times SHROUT). Merge the eligible CRSP observations with the CZ signals using permno and yyyymm.

3. For each of the three signals (BMCZ, GPCZ, and Dur), construct decile portfolios using NYSE breakpoints and annual rebalancing at the end of June. Create two types of decile portfolios for each signal:
   (i) Value-weighted, rebalanced annually at June, with NYSE breakpoints.
   (ii) Equal-weighted, rebalanced annually at June, with NYSE breakpoints.
   For each portfolio type, this should produce 10 BM portfolios, 10 GP portfolios, and 10 duration portfolios, giving 30 portfolios in total.

4. For each month \tau, calculate the next-month excess return for every portfolio using CRSP stock returns and the risk-free rate from Q3_Datasets/fama_french.csv.Extract the monthly observations and the RF column from the Fama–French dataset, convert RF from percentages to decimals by dividing by 100, and align the risk-free rate with the corresponding portfolio return month. Define the next-month portfolio excess return as xR_{p,\tau+1}=R_{p,\tau+1}-RF_{\tau+1}. For value-weighted portfolios, use the appropriate lagged market-equity weights. For equal-weighted portfolios, assign equal weight to each eligible constituent stock. Ensure that portfolio assignments, weights, stock returns, and risk-free rates are correctly aligned, with no look-ahead bias.

5. For each portfolio p and month \tau, calculate the average BM, GP, and duration decile ranks of the firms belonging to that portfolio.
   First, for each month \tau, assign eligible stocks to cross-sectional deciles from 1 to 10 for each of the three signals. Define the stock-level decile variables as Q^{BM}_{j,\tau}, Q^{GP}_{j,\tau}, and Q^{Dur}_{j,\tau}, respectively.
   Then, for each portfolio, calculate the average decile rank of its constituent firms for each characteristic. Define these portfolio-level variables as
   Dec^{BM}_{p,\tau},
   Dec^{GP}_{p,\tau},
   Dec^{Dur}_{p,\tau}.
   Calculate these averages using the firms belonging to the portfolio in month \tau, including the decile ranks of characteristics other than the one used to form that portfolio. Use the same cross-sectional decile definitions for both the value-weighted and equal-weighted portfolio analyses.
   Align these month-\tau portfolio characteristics with portfolio excess returns in month \tau+1.

6. Estimate the following seven pooled panel regression specifications using the 30 portfolios described above:
   (i) xR_{p,\tau+1}=a+b_{BM}Dec^{BM}_{p,\tau}+\epsilon_{p,\tau+1}
   (ii) xR_{p,\tau+1}=a+b_{GP}Dec^{GP}_{p,\tau}+\epsilon_{p,\tau+1}
   (iii) xR_{p,\tau+1}=a+b_{Dur}Dec^{Dur}_{p,\tau}+\epsilon_{p,\tau+1}
   (iv) xR_{p,\tau+1}=a+b_{BM}Dec^{BM}_{p,\tau}+b_{GP}Dec^{GP}_{p,\tau}+\epsilon_{p,\tau+1}
   (v) xR_{p,\tau+1}=a+b_{Dur}Dec^{Dur}_{p,\tau}+b_{BM}Dec^{BM}_{p,\tau}+\epsilon_{p,\tau+1}
   (vi) xR_{p,\tau+1}=a+b_{Dur}Dec^{Dur}_{p,\tau}+b_{GP}Dec^{GP}_{p,\tau}+\epsilon_{p,\tau+1}
   (vii) xR_{p,\tau+1}=a+b_{Dur}Dec^{Dur}_{p,\tau}+b_{BM}Dec^{BM}_{p,\tau}+b_{GP}Dec^{GP}_{p,\tau}+\epsilon_{p,\tau+1}

7. For each of the seven specifications, estimate the panel regressions using pooled OLS with Driscoll and Kraay (1998) standard errors.
   Estimate each specification separately using:
   (a) The 30 value-weighted portfolios.
   (b) The 30 equal-weighted portfolios.
   This should produce 14 sets of panel regression results in total.

8. For each specification and both portfolio-weighting methods, report the pooled OLS coefficient estimates and their Driscoll–Kraay t-statistics, including the intercept. Report coefficients in monthly percentage points. Save the coefficient estimates, standard errors, t-statistics, number of portfolio-month observations, and the bandwidth or lag length used.

9. Generate one LaTeX table containing all seven specifications for both value-weighted and equal-weighted portfolios. Organize the table into two panels:
   Panel A: Value-weighted portfolios.
   Panel B: Equal-weighted portfolios.
   Use the seven regression specifications as columns. Report the coefficient estimates and their Driscoll–Kraay t-statistics in parentheses below each estimate. Include the intercept and the coefficients on BM, GP, and duration. Leave cells blank when a characteristic is not included in a specification.
   Add statistical significance stars to the coefficient estimates using the corresponding Driscoll–Kraay t-statistics. Use *** for significance at the 1% level, ** for 5%, and * for 10%, based on two-sided tests and unrounded statistics. Place the stars as superscripts after each coefficient estimate.
   Include the number of portfolio-month observations and notes explaining the portfolio formation method, portfolio-level average decile variables, estimation method, and standard-error method.

10. Save the final regression summaries and the portfolio-month panel dataset as CSV files in the output/ folder. Save the LaTeX table as Q3e_Pooled_OLS.tex in the same folder. Insert the table under Question 3(e) in solution.tex. 