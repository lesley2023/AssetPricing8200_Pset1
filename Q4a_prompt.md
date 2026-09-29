Provide me with Python code following these steps:

1. Read the csv file “Bond Dataset.csv” into a pandas DataFrame.
2. Display the first few rows and the unique values of “TTERMLBL” to get an overview of the data.
3. Keep only the Fama-Bliss Discount Bond (Nominal) series for maturities H=1,2,3,4,5.
The relevant variables are:
- MCALDT: date
- TTERMLBL: bond maturity
- TMYTM: yield to maturity in percentage terms
4. Create a monthly date variable using “MCALDT”, extract the maturity H from “TTERMLBL”, and sort the data chronologically.
5. Convert TMYTM from percentage terms to decimal yields:
Y_{b,t}^{(H)} = TMYTM/100.
Then reshape the data so that each row represents one month and contains the yields for H=1,2,3,4,5.
6. For each H=1,2,3,4,5, construct the log yield
y_{b,t}^{(H)}=\log(1+Y_{b,t}^{(H)}).
7. Construct the log forward rates. Define
f_{b,t}^{(1)}=y_{b,t}^{(1)}.
For H=2,3,4,5, define
f_{b,t}^{(H)} = Hy_{b,t}^{(H)}- (H-1)y_{b,t}^{(H-1)}
Both yields in this formula should come from the same month t.
8. Construct the log annual bond returns. Define
r_{b,t}^{(1)}=y_{b,t-12}^{(1)}.
For H=2,3,4,5, define
r_{b,t}^{(H)} = Hy_{b,t-12}^{(H)} - (H-1)y_{b,t}^{(H-1)}
Be careful with the timing: the first term uses the H-year yield from the previous period, while the second term uses the (H-1)-year yield from the current period. 
9. For H=2,3,4,5, construct the excess log yields:
xy_{b,t}^{(H)} = y_{b,t}^{(H)}-y_{b,t}^{(1)}.
10. Construct the excess log forward rates:
xf_{b,t}^{(H)}= f_{b,t}^{(H)}-f_{b,t}^{(1)}.
11. Construct the excess log annual returns:
xr_{b,t}^{(H)} = r_{b,t}^{(H)}-r_{b,t}^{(1)}.
12. For each H=2,3,4,5, calculate and report the time-series averages of xy, xf, and xr in one table.
13. Check for missing values and use only the available observations when calculating each average. Do not replace missing values with zeros.
14. When displaying the final table, multiply the average xy, xf, and xr values by 100 so that they are reported in percentage terms. Clearly label the table to indicate that the reported values are in percent.
15. Please keep the Python code straightforward. Use pandas and numpy, and add brief comments explaining the important steps.
