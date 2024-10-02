import numpy as np
import pandas as pd

# Define the mean and standard deviation (in decimal form)
mean = 0.1048  # 10.48%
fee = .012
std_dev = 0.1272  # 12.72%
inflation = .03
mean = mean - inflation - fee

# Define the number of years and simulations
n_years = 30  # 30-year period
n_simulations = 1000  # 1000 simulations

# Step 1: Generate returns using the equivalent formula to Excel
# Simulating 30 years (columns) for 1000 rows (simulations)
excel_style_returns = mean + std_dev * np.random.normal(0, 1, (n_years, n_simulations))

# Step 2: Convert to cumulative returns (start with $1 investment, then calculate cumulative return over time)
cumulative_returns = np.cumprod(1 + excel_style_returns, axis=0)

# Step 3: Calculate the Ending Value for each simulation after 30 years
ending_values = cumulative_returns[-1, :]  # Ending value for each simulation

# Step 4: Calculate the CAGR for each simulation
start_value = 1  # Assuming the initial investment is $1
cagr = (ending_values / start_value) ** (1 / n_years) - 1

# Step 5: Calculate percentiles from 0% to 100% in 1% increments for the CAGR
cagr_percentiles = np.percentile(cagr, np.arange(0, 101, 1))

# Step 6: Convert the result to a pandas DataFrame and display it
cagr_percentile_df = pd.DataFrame({
    'Percentile (%)': np.arange(0, 101, 1),
    '30-Year CAGR': cagr_percentiles
})

# Display the DataFrame
# Save the DataFrame to a CSV file
cagr_percentile_df.to_csv('30_year_cagr_percentiles.csv', index=False)

# Notify that the file has been saved
print("The 30-Year CAGR Percentiles have been saved to '30_year_cagr_percentiles.csv'")