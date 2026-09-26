# Question 3(c) changes

- Added `Q3c.py` to merge the three Chen--Zimmermann signals with the eligible CRSP universe and construct the five requested decile-portfolio variants.
- Used prior-month signals for monthly portfolios, June signals for the following July--June annual holding period, and lagged market equity for value weights.
- Calculated monthly excess returns using the Fama--French risk-free rate.
- Generated five scatterplots containing BMCZ, MOMCZ, and GPCZ and a 15-row HML summary with Newey--West (1987) standard errors and the Newey--West (1994) automatic lag rule.
- Added only the five figures and the HML table to Question 3(c) in `solution.tex`, without prose discussion.
