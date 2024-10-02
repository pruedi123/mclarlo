import numpy as np
import pandas as pd

# Define the mean and standard deviation (in decimal form)
mean = 0.1048  # 10.48%
fee = .012
mean = mean - fee
std_dev = 0.1272  # 12.72%

# Define the number of years and simulations
n_years = 20  # 29 years remaining
n_simulations = 2000  # 2000 simulations

# Function to simulate returns and calculate the percentage of ending values > 0
def simulate_withdrawals(portfolio_value, withdrawal_amount):
    # Generate returns for 29 years
    excel_style_returns = (mean - 0.03) + std_dev * np.random.normal(0, 1, (n_years, n_simulations))
    
    ending_balances = []

    # Simulate each year's portfolio values
    for simulation in range(n_simulations):
        current_portfolio = portfolio_value
        for year in range(n_years):
            current_portfolio -= withdrawal_amount
            if current_portfolio <= 0:
                current_portfolio = 0
                break  # Stop if portfolio is depleted
            current_portfolio *= (1 + excel_style_returns[year, simulation])

        ending_balances.append(current_portfolio)

    # Calculate the percentage of simulations with a positive ending balance
    percentage_above_zero = np.mean(np.array(ending_balances) > 0) * 100
    return percentage_above_zero

# Binary search to find the required portfolio value for target success rate
def find_required_portfolio(withdrawal_amount, target_percentage, tolerance=0.01):
    low = 500000  # Lower bound for portfolio value
    high = 5000000  # Upper bound for portfolio value
    best_portfolio_value = (low + high) / 2
    portfolios_in_range = []  # To store portfolios within the tolerance range

    while high - low > tolerance:
        mid = (low + high) / 2
        percentage_above_zero = simulate_withdrawals(mid, withdrawal_amount)

        # Check if the percentage is within the tolerance range of the target
        if abs(percentage_above_zero - target_percentage) <= 0.5:
            portfolios_in_range.append(mid)  # Add to the list of valid portfolios

        # Adjust the search range
        if percentage_above_zero > target_percentage:
            high = mid  # Decrease the portfolio value if more than target percentage have a positive balance
        else:
            low = mid  # Increase the portfolio value if less than target percentage have a positive balance

        print(f"Testing Portfolio: ${mid:.2f}, Percentage > 0: {percentage_above_zero:.2f}% (Target: {target_percentage}%)")

    # Calculate the average of portfolio values within tolerance range
    if portfolios_in_range:
        optimal_portfolio_value = np.mean(portfolios_in_range)
    else:
        optimal_portfolio_value = best_portfolio_value  # If no values in range, return the last best value

    return optimal_portfolio_value

# Find the required portfolio value for multiple target percentages
def find_portfolio_values_for_targets(target_percentages, withdrawal_amount):
    portfolio_values = {}
    for target in target_percentages:
        print(f"\nCalculating for target: {target}%")
        portfolio_value = find_required_portfolio(withdrawal_amount, target)
        portfolio_values[target] = portfolio_value
        print(f"Required Portfolio for {target}% success rate: ${portfolio_value:.2f}")
    
    return portfolio_values

# Specify the withdrawal amount for 29 years
withdrawal_amount = 45991  # Example withdrawal rate

# Specify target percentages (75%, 85%, and 95%)
target_percentages = [85, 75, 95]

# Run the process for all targets to calculate required portfolio values
portfolio_values = find_portfolio_values_for_targets(target_percentages, withdrawal_amount)

# Display the results
print("\nFinal required portfolio values for each target:")
for target, value in portfolio_values.items():
    print(f"{target}% success rate: ${value:.2f}")