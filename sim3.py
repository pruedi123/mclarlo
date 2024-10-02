import numpy as np
import pandas as pd
import multiprocessing as mp
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Investment Parameters
mean_return = 0.1048        # Expected annual return (10.48%)
fee = 0.012                 # Annual fee (1.2%)
mean_return -= fee          # Adjusted mean return after fees
std_dev = 0.1272            # Annual standard deviation (12.72%)

# Simulation Parameters
n_years_total = 30          # Total number of years
n_simulations = 2000        # Number of Monte Carlo simulations
initial_portfolio = 1000000 # Starting portfolio value ($1,000,000)
inflation_rate = 0.03       # Assuming real returns (inflation-adjusted)

# Withdrawal Adjustment Parameters
target_success_rate = 85    # Target probability of success (%)
lower_threshold = 75        # Lower threshold for withdrawal adjustment (%)
upper_threshold = 95        # Upper threshold for withdrawal adjustment (%)
withdrawal_cap = None       # Maximum withdrawal amount (set to None if no cap)
withdrawal_floor = None     # Minimum withdrawal amount (set to None if no floor)

# Inner Simulation Parameter
n_inner_simulations = 100   # Reduced number of simulations for success rate calculations

# Output File
output_file = 'retirement_simulation_results.xlsx'

# Function definitions...

# Function to calculate the initial withdrawal amount for Year 1
def calculate_initial_withdrawal():
    def simulate_withdrawals(withdrawal_amount):
        excel_style_returns = (mean_return - inflation_rate) + std_dev * np.random.normal(
            0, 1, (n_years_total, n_simulations)
        )
        ending_values = []

        for simulation in range(n_simulations):
            portfolio_value = initial_portfolio

            for year in range(n_years_total):
                portfolio_value -= withdrawal_amount
                if portfolio_value <= 0:
                    portfolio_value = 0
                    break
                annual_return = excel_style_returns[year, simulation]
                portfolio_value *= (1 + annual_return)

            ending_values.append(portfolio_value)

        percentage_above_zero = np.mean(np.array(ending_values) > 0) * 100
        return percentage_above_zero

    # Binary search to find the optimal initial withdrawal amount
    low = 0
    high = initial_portfolio
    tolerance = 0.01
    tolerance_percentage = 0.5
    max_iterations = 20  # Limit the number of iterations

    withdrawals_in_range = []

    for _ in range(max_iterations):
        mid = (low + high) / 2
        success_rate = simulate_withdrawals(mid)

        if abs(success_rate - target_success_rate) <= tolerance_percentage:
            withdrawals_in_range.append(mid)
            break  # Accept the withdrawal amount within tolerance

        if success_rate > target_success_rate:
            low = mid
        else:
            high = mid

        if high - low < tolerance:
            break

    if withdrawals_in_range:
        optimal_withdrawal = np.mean(withdrawals_in_range)
    else:
        optimal_withdrawal = mid

    return optimal_withdrawal

# Function to simulate portfolio over the remaining years and calculate success rate
def calculate_success_rate(portfolio_balance, withdrawal_amount, years_remaining):
    # Use reduced number of simulations for inner calculations
    excel_style_returns = (mean_return - inflation_rate) + std_dev * np.random.normal(
        0, 1, (years_remaining, n_inner_simulations)
    )
    ending_values = []

    for simulation in range(n_inner_simulations):
        portfolio_value = portfolio_balance

        for year in range(years_remaining):
            portfolio_value -= withdrawal_amount
            if portfolio_value <= 0:
                portfolio_value = 0
                break
            annual_return = excel_style_returns[year, simulation]
            portfolio_value *= (1 + annual_return)

        ending_values.append(portfolio_value)

    success_rate = np.mean(np.array(ending_values) > 0) * 100
    return success_rate

# Function to adjust withdrawal amount based on success rate
def adjust_withdrawal(portfolio_balance, years_remaining, current_withdrawal):
    success_rate = calculate_success_rate(portfolio_balance, current_withdrawal, years_remaining)

    if success_rate < lower_threshold or success_rate > upper_threshold:
        # Binary search to find the adjusted withdrawal amount
        low = 0
        high = portfolio_balance
        tolerance = 0.01
        tolerance_percentage = 0.5
        max_iterations = 10  # Limit the number of iterations

        withdrawals_in_range = []

        for _ in range(max_iterations):
            mid = (low + high) / 2
            new_success_rate = calculate_success_rate(portfolio_balance, mid, years_remaining)

            if abs(new_success_rate - target_success_rate) <= tolerance_percentage:
                withdrawals_in_range.append(mid)
                break  # Accept the withdrawal amount within tolerance

            if new_success_rate > target_success_rate:
                low = mid
            else:
                high = mid

            if high - low < tolerance:
                break

        if withdrawals_in_range:
            adjusted_withdrawal = np.mean(withdrawals_in_range)
        else:
            adjusted_withdrawal = mid

        # Apply withdrawal cap and floor if specified
        if withdrawal_cap is not None:
            adjusted_withdrawal = min(adjusted_withdrawal, withdrawal_cap)
        if withdrawal_floor is not None:
            adjusted_withdrawal = max(adjusted_withdrawal, withdrawal_floor)

        return adjusted_withdrawal
    else:
        return current_withdrawal

# Function to run a single simulation (for multiprocessing)
def run_single_simulation(args):
    simulation, initial_withdrawal = args
    portfolio_balance = initial_portfolio
    years_remaining = n_years_total
    withdrawal_amount = initial_withdrawal
    simulation_data = {}
    annual_returns = []  # To store annual returns for CAGR calculation

    for year in range(1, n_years_total + 1):
        # Record the beginning balance
        begin_balance = portfolio_balance

        # Subtract withdrawal from portfolio balance
        withdrawal = withdrawal_amount
        net_begin = portfolio_balance - withdrawal

        if net_begin <= 0:
            net_begin = 0
            portfolio_balance = 0
            # Record data for the current year
            simulation_data[f'Year {year} Begin Bal'] = begin_balance
            simulation_data[f'Year {year} Withdrawal'] = 0
            simulation_data[f'Year {year} Net Begin'] = 0
            simulation_data[f'Year {year} Return'] = 0
            simulation_data[f'Year {year} End Balance'] = 0
            break  # Portfolio depleted, exit the year loop

        # Apply investment return
        annual_return = (mean_return - inflation_rate) + std_dev * np.random.normal(0, 1)
        ending_balance = net_begin * (1 + annual_return)

        # Store the annual return for CAGR calculation
        annual_returns.append(annual_return)

        # Update years remaining
        years_remaining -= 1

        # Adjust withdrawal amount for next year if necessary
        if years_remaining > 0:
            withdrawal_amount = adjust_withdrawal(ending_balance, years_remaining, withdrawal_amount)

        # Record data for the current year
        simulation_data[f'Year {year} Begin Bal'] = begin_balance
        simulation_data[f'Year {year} Withdrawal'] = withdrawal
        simulation_data[f'Year {year} Net Begin'] = net_begin
        simulation_data[f'Year {year} Return'] = annual_return
        simulation_data[f'Year {year} End Balance'] = ending_balance

        # Prepare for next iteration
        portfolio_balance = ending_balance

    # Calculate CAGR for the simulation
    if len(annual_returns) > 0:
        cumulative_return = np.prod([1 + r for r in annual_returns])
        cagr = cumulative_return**(1 / len(annual_returns)) - 1
    else:
        cagr = 0  # If the portfolio was depleted in the first year

    simulation_data['CAGR'] = cagr

    return simulation_data

# Main execution block
if __name__ == '__main__':
    # Suppress warnings for cleaner output
    warnings.filterwarnings('ignore')

    # Calculate the initial withdrawal amount
    initial_withdrawal = calculate_initial_withdrawal()
    print(f"Calculated initial withdrawal amount: ${initial_withdrawal:.2f}")

    # Prepare arguments for multiprocessing
    args_list = [(simulation, initial_withdrawal) for simulation in range(n_simulations)]

    # Run simulations in parallel
    with mp.Pool(processes=mp.cpu_count()) as pool:
        results = pool.map(run_single_simulation, args_list)

    # Convert the list of simulation data into a DataFrame
    df_simulation_results = pd.DataFrame(results)

    # Extract Annual Returns
    # Get list of annual return columns
    annual_return_columns = [col for col in df_simulation_results.columns if 'Year' in col and 'Return' in col]

    # Extract those columns
    df_annual_returns = df_simulation_results[annual_return_columns]

    # Optionally, you can rename the columns to 'Year 1', 'Year 2', etc.
    df_annual_returns.columns = [f'Year {i+1}' for i in range(len(annual_return_columns))]

    # Calculate CAGR Percentiles
    cagr_values = df_simulation_results['CAGR']
    percentiles = np.arange(0, 101, 1)
    cagr_percentiles = np.percentile(cagr_values, percentiles)
    df_cagr_percentiles = pd.DataFrame({
        'Percentile': percentiles,
        'CAGR': cagr_percentiles * 100  # Convert to percentage
    })

    # **Extract Annual Withdrawals and Prepare DataFrame**
    # Get list of annual withdrawal columns
    annual_withdrawal_columns = [col for col in df_simulation_results.columns if 'Year' in col and 'Withdrawal' in col]

    # Extract those columns
    df_withdrawals = df_simulation_results[annual_withdrawal_columns]

    # Calculate the average withdrawal per simulation across all years
    df_withdrawals['Average Withdrawal'] = df_withdrawals.mean(axis=1)

    # Reorder columns to have 'Average Withdrawal' at the beginning
    cols = ['Average Withdrawal'] + [col for col in df_withdrawals.columns if col != 'Average Withdrawal']
    df_withdrawals = df_withdrawals[cols]

    # **Calculate Percentiles for Average Annual Withdrawals**
    average_withdrawals = df_withdrawals['Average Withdrawal'].values
    withdrawal_percentiles = np.percentile(average_withdrawals, percentiles)
    df_withdrawal_percentiles = pd.DataFrame({
        'Percentile': percentiles,
        'Average Withdrawal': withdrawal_percentiles
    })

    # Save the results to an Excel file with multiple sheets
    with pd.ExcelWriter(output_file) as writer:
        df_simulation_results.to_excel(writer, sheet_name='Simulations', index=False)
        df_cagr_percentiles.to_excel(writer, sheet_name='CAGR Percentiles', index=False)
        df_annual_returns.to_excel(writer, sheet_name='Annual Returns', index=False)
        df_withdrawals.to_excel(writer, sheet_name='Annual Withdrawals', index=False)
        df_withdrawal_percentiles.to_excel(writer, sheet_name='Withdrawal Percentiles', index=False)

    print(f"Simulation results saved to '{output_file}'")

    # Display the first few rows of the results
    print(df_simulation_results.head())
    print("\nCAGR Percentiles:")
    print(df_cagr_percentiles.head(10))
    print("\nWithdrawal Percentiles:")
    print(df_withdrawal_percentiles.head(10))