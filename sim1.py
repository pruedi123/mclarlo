import numpy as np
import pandas as pd

# Define the mean and standard deviation (in decimal form)
mean = 0.1048  # 10.48%
fee = .012
mean = mean - fee
std_dev = 0.1272  # 12.72%

# Define the number of years and simulations
n_years = 30  # 30-year period
n_simulations = 2000  # 2000 simulations

# Function to simulate returns and calculate the percentage of ending values > 0
def simulate_withdrawals(withdrawal_amount):
    # Step 1: Generate returns using the equivalent formula to Excel
    excel_style_returns = (mean - 0.03) + std_dev * np.random.normal(0, 1, (n_years, n_simulations))  # Using 3% inflation to get real return

    # Step 2: Initialize the portfolio values with the initial investment of $1,000,000
    initial_investment = 1000000
    ending_values = []  # To store the final ending balance for each simulation

    # Step 3: Simulate each year's portfolio values
    for simulation in range(n_simulations):
        portfolio_value = initial_investment

        for year in range(n_years):
            # Subtract the withdrawal
            portfolio_value -= withdrawal_amount
            if portfolio_value <= 0:
                portfolio_value = 0
                break  # Stop if portfolio is depleted

            # Apply the return for that year
            annual_return = excel_style_returns[year, simulation]
            portfolio_value *= (1 + annual_return)

        # Store the ending value of the portfolio for the simulation
        ending_values.append(portfolio_value)

    # Step 4: Calculate the percentage of simulations with a positive ending balance
    ending_values_array = np.array(ending_values)
    percentage_above_zero = np.mean(ending_values_array > 0) * 100
    return percentage_above_zero

# Binary search to find the optimal withdrawal amount for a given target percentage
def find_optimal_withdrawal(target_percentage, tolerance=0.01):  # Reduced tolerance for finer search
    low = 10000  # Lower bound for withdrawal amount
    high = 100000  # Upper bound for withdrawal amount
    best_withdrawal = (low + high) / 2
    withdrawals_in_range = []  # To store withdrawals within the tolerance range
    tolerance_percentage = 0.5  # Tolerance for the percentage range

    while high - low > tolerance:
        mid = (low + high) / 2
        percentage_above_zero = simulate_withdrawals(mid)

        # Check if the percentage is within the tolerance range of the target
        if abs(percentage_above_zero - target_percentage) <= tolerance_percentage:
            withdrawals_in_range.append(mid)  # Add to the list of valid withdrawals

        # Adjust the search range
        if percentage_above_zero > target_percentage:
            low = mid  # Increase withdrawal if more than the target percentage have a positive balance
        else:
            high = mid  # Decrease withdrawal if less than the target percentage have a positive balance

        print(f"Testing withdrawal: ${mid:.2f}, Percentage > 0: {percentage_above_zero:.2f}% (Target: {target_percentage}%)")

    # Calculate the average of withdrawals within the tolerance range
    if withdrawals_in_range:
        optimal_withdrawal = np.mean(withdrawals_in_range)
    else:
        optimal_withdrawal = best_withdrawal  # If no values in range, return the last best value

    return optimal_withdrawal

# Find the optimal withdrawal amounts for multiple target percentages
def find_withdrawals_for_targets(target_percentages):
    optimal_withdrawals = {}
    for target in target_percentages:
        print(f"\nCalculating for target: {target}%")
        optimal_withdrawal = find_optimal_withdrawal(target_percentage=target)
        optimal_withdrawals[target] = optimal_withdrawal
        print(f"Optimal Withdrawal for {target}% success rate: ${optimal_withdrawal:.2f}")
    
    return optimal_withdrawals

# Specify target percentages (85%, 75%, and 95%)
target_percentages = [85, 75, 95]

# Run the process for all targets
optimal_withdrawals = find_withdrawals_for_targets(target_percentages)

# Display the results
print("\nFinal optimal withdrawals for each target:")
for target, withdrawal in optimal_withdrawals.items():
    print(f"{target}% success rate: ${withdrawal:.2f}")