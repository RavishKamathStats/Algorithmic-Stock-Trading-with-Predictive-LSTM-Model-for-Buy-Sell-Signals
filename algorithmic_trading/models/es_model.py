import warnings
warnings.filterwarnings("ignore", category=FutureWarning, message="is_sparse is deprecated and will be removed in a future version")
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.graphics.tsaplots import plot_acf
from statsmodels.tsa.stattools import adfuller
from pmdarima.arima.utils import ndiffs  # For automatic differencing
import os

class ExponentialSmoothingModel:
    def __init__(self, db):
        self.db = db

    def get_stock_data(self, portfolio_id, ticker):
        query = '''
            SELECT date, adj_close
            FROM stock_data
            WHERE ticker = %s AND ticker IN (
                SELECT ticker FROM portfolio_stocks
                WHERE portfolio_id = %s
            )
            ORDER BY date
        '''
        stock_data = self.db.fetch_query(query, (ticker, portfolio_id))
        df = pd.DataFrame(stock_data, columns=['Date', 'Adj Close'])
        df.set_index('Date', inplace=True)
        return df

    def detect_trend(self, df):
        print("Checking for trend using ADF test...")
        result = adfuller(df['Adj Close'])
        p_value = result[1]
        print(f"Initial ADF Statistic: {result[0]}")
        print(f"Initial p-value: {p_value:.4f}")
        
        if p_value > 0.05:  # p-value greater than 0.05 indicates non-stationarity, suggesting a trend
            print(f"Non-stationarity detected with p-value {p_value:.4f}. Differencing needed.")
            df, d = self.make_stationary(df)
            return df, d
        else:
            print("Data is already stationary. No differencing needed.")
            return df, 0  # No differencing required

    def make_stationary(self, df):
        print("Making data stationary...")
        d = ndiffs(df['Adj Close'], test='adf')  # Check the number of differences needed
        if d > 0:
            print(f"Differencing applied (d={d}).")
            df['Adj Close Diff'] = df['Adj Close'].diff(d)
            df = df.dropna()  # Remove rows with NaN values after differencing

            # Re-check stationarity after differencing by performing the ADF test again
            result = adfuller(df['Adj Close Diff'])
            new_p_value = result[1]
            print(f"New ADF Statistic: {result[0]}")
            print(f"New p-value after differencing: {new_p_value:.4f}")
            
            if new_p_value <= 0.05:
                print(f"The data is now stationary after differencing with p-value: {new_p_value:.4f}.")
            else:
                print(f"The data is still not stationary even after differencing. p-value: {new_p_value:.4f}")
        else:
            print("Data does not require differencing.")
        return df, d  # Return the stationary data and the differencing order

    def plot_original_data(self, df, stock_name):
        plt.figure(figsize=(12, 6))
        plt.plot(df['Adj Close'], label=f"{stock_name} Adjusted Close Price", alpha=0.5)
        plt.title(f"Original Data for {stock_name}")
        plt.xlabel('Date')
        plt.ylabel('Adjusted Close Price')
        plt.legend()

        output_dir = os.path.join("plots", "ES_model")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        output_file = os.path.join(output_dir, f"{stock_name}_original_data.png")
        plt.savefig(output_file)
        print(f"Original data plot saved as {output_file}")
        plt.close()

    def plot_acf_and_save(self, df, stock_name):
        """Plot the ACF (autocorrelation function) and save it in the ES_model directory."""
        plt.figure(figsize=(10, 6))
        plot_acf(df['Adj Close Diff'], lags=50)
        plt.title(f"ACF for {stock_name}")
        
        output_dir = os.path.join("plots", "ES_model")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        output_file = os.path.join(output_dir, f"{stock_name}_acf_plot.png")
        plt.savefig(output_file)
        print(f"ACF plot saved as {output_file}")
        plt.close()

    def run_exponential_smoothing(self, df, trend=None, seasonal=None, seasonal_periods=None):
        model = ExponentialSmoothing(df['Adj Close Diff'], trend=trend, seasonal=seasonal, seasonal_periods=seasonal_periods)
        fitted_model = model.fit()
        df['Fitted Diff'] = fitted_model.fittedvalues
        return df, fitted_model

    def reconstruct_fitted_values(self, fitted_model, df_original, d):
        if d > 0:
            fitted_reconstructed = df_original['Adj Close'].iloc[0] + fitted_model.fittedvalues.cumsum()
            df_original['Fitted Original'] = fitted_reconstructed
        else:
            df_original['Fitted Original'] = fitted_model.fittedvalues

        return df_original

    def generate_buy_sell_signals(self, df, df_original):
        df['Buy_Signal'] = df.apply(lambda x: x['Adj Close Diff'] if x['Adj Close Diff'] > x['Fitted Diff'] else None, axis=1)
        df['Sell_Signal'] = df.apply(lambda x: x['Adj Close Diff'] if x['Adj Close Diff'] < x['Fitted Diff'] else None, axis=1)

        # Map the buy/sell signals from the differenced data to the original data
        df_original['Buy_Signal'] = None
        df_original['Sell_Signal'] = None
        for i in df.index:
            if pd.notnull(df.at[i, 'Buy_Signal']):
                df_original.at[i, 'Buy_Signal'] = df_original.at[i, 'Adj Close']  
            if pd.notnull(df.at[i, 'Sell_Signal']):
                df_original.at[i, 'Sell_Signal'] = df_original.at[i, 'Adj Close']  

        return df_original

    def plot_exponential_smoothing(self, df_original, stock_name):
        plt.figure(figsize=(12, 6))
        plt.plot(df_original['Adj Close'], label=f'{stock_name} Adjusted Close', alpha=0.5)
        plt.plot(df_original['Fitted Original'], label=f'{stock_name} Exponential Smoothing Curve', alpha=0.75, color='orange')
        plt.scatter(df_original.index, df_original['Buy_Signal'], label="Buy Signal", marker='^', color='green', alpha=1)
        plt.scatter(df_original.index, df_original['Sell_Signal'], label="Sell Signal", marker='v', color='red', alpha=1)
        
        plt.title(f"{stock_name} Exponential Smoothing Model with Buy/Sell Signals")
        plt.xlabel('Date')
        plt.ylabel('Adjusted Close Price')
        plt.legend()

        output_dir = os.path.join("plots", "ES_model")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        output_file = os.path.join(output_dir, f"{stock_name}_exponential_smoothing_with_signals.png")
        plt.savefig(output_file)
        print(f"Plot saved as {output_file}")
        plt.close()

    def run_model(self, portfolio_id, stock_name, seasonal=None, seasonal_periods=None):
        df_original = self.get_stock_data(portfolio_id, stock_name)
        df, d = self.detect_trend(df_original.copy())
        df, fitted_model = self.run_exponential_smoothing(df, trend='add' if d > 0 else None, seasonal=seasonal, seasonal_periods=seasonal_periods)
        df_original = self.reconstruct_fitted_values(fitted_model, df_original, d)
        df_original = self.generate_buy_sell_signals(df, df_original)
        self.plot_exponential_smoothing(df_original, stock_name)