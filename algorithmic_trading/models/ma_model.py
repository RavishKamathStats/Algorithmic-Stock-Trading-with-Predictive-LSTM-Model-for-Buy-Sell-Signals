import warnings
warnings.filterwarnings("ignore", category=FutureWarning, message="is_sparse is deprecated and will be removed in a future version")
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from statsmodels.tsa.stattools import adfuller
from pmdarima.arima.utils import ndiffs  # For automatic differencing
import os
from datetime import datetime

class MAModel:
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

    def check_stationarity(self, df):
        result = adfuller(df['Adj Close'])
        p_value = result[1]
        print(f"ADF Statistic: {result[0]}")
        print(f"p-value: {p_value}")

        if p_value <=0.05:
            return
        else:
            print(f"p value is high indicating a need for stationary process with p value: {p_value:.4f}")

        return p_value <= 0.05 

    def make_stationary(self, df):
        print("Making data stationary...")
        d = ndiffs(df['Adj Close'], test='adf')
        if d > 0:
            print(f"Differencing applied (d={d}).")
            df['Adj Close'] = df['Adj Close'].diff(d)
            df = df.dropna()
            # Re-check stationarity after differencing
            result = adfuller(df['Adj Close'])
            new_p_value = result[1]
            print(f"New ADF Statistic: {result[0]}")
            print(f"New p-value after differencing: {round(new_p_value)}")
            if new_p_value <= 0.05:
                print(f"The data is now stationary after differencing with p-value: {round(new_p_value)}.")
            else:
                print(f"The data is still not stationary even after differencing. p-value: {new_p_value:.4f}")
        return df, d 

    def calculate_moving_averages(self, df, short_window, long_window):
        df['Short_MA'] = df['Adj Close'].rolling(window=short_window, min_periods=1).mean()
        df['Long_MA'] = df['Adj Close'].rolling(window=long_window, min_periods=1).mean()
        return df

    def generate_buy_sell_signals(self, df):
        df['Buy_Signal'] = np.where(df['Short_MA'] > df['Long_MA'], df['Adj Close'], np.nan)
        df['Sell_Signal'] = np.where(df['Short_MA'] < df['Long_MA'], df['Adj Close'], np.nan)
        return df

    def plot_signals_on_original_data(self, df_original, df_stationary, stock_name, short_window, long_window):
        df_original['Short_MA'] = df_original['Adj Close'].rolling(window=short_window, min_periods=1).mean()
        df_original['Long_MA'] = df_original['Adj Close'].rolling(window=long_window, min_periods=1).mean()
        buy_signals_idx = df_stationary.index[df_stationary['Buy_Signal'].notna()]
        sell_signals_idx = df_stationary.index[df_stationary['Sell_Signal'].notna()]
        buy_signals_on_original = df_original.loc[buy_signals_idx, 'Adj Close']
        sell_signals_on_original = df_original.loc[sell_signals_idx, 'Adj Close']
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(df_original['Adj Close'], label=f"{stock_name} Adjusted Close Price", alpha=0.5)
        ax.plot(df_original['Short_MA'], label=f"{short_window}-Day MA", color='blue', alpha=0.7)
        ax.plot(df_original['Long_MA'], label=f"{long_window}-Day MA", color='orange', alpha=0.7)
        ax.scatter(buy_signals_on_original.index, buy_signals_on_original, label="Buy Signal", marker='^', color='green', alpha=1)
        ax.scatter(sell_signals_on_original.index, sell_signals_on_original, label="Sell Signal", marker='v', color='red', alpha=1)
        ax.set_title(f"{stock_name} Buy/Sell Signals with Moving Averages on Original Data")
        ax.set_xlabel('Date')
        ax.set_ylabel('Adjusted Close Price')
        ax.legend()

        output_dir = os.path.join("plots", "MA_model")
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        output_file = os.path.join(output_dir, f"{stock_name}_buy_sell_signals_with_moving_averages_{timestamp}.png")
        fig.savefig(output_file)
        print(f"Plot saved as {output_file}")
        plt.close(fig)

    def save_stationary_plot(self, df_stationary, stock_name, d):
        if d > 0:
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(df_stationary['Adj Close'], label=f"{stock_name} Differenced (d={d}) Adjusted Close", alpha=0.7)
            ax.set_title(f"{stock_name} Stationary Data After Differencing (d={d})")
            ax.set_xlabel('Date')
            ax.set_ylabel('Adjusted Close Price')
            ax.legend()
            output_dir = os.path.join("plots", "MA_model")
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, f"{stock_name}_stationary_differenced_d{d}.png")
            fig.savefig(output_file)
            print(f"Stationary plot saved as {output_file}")
            plt.close(fig)


    def run_model(self, portfolio_id, stock_name, short_window, long_window):
        df_original = self.get_stock_data(portfolio_id, stock_name)
        df_stationary = df_original.copy()
        if not self.check_stationarity(df_stationary):
            df_stationary, d = self.make_stationary(df_stationary)
            self.save_stationary_plot(df_stationary, stock_name, d)
        df_stationary = self.calculate_moving_averages(df_stationary, short_window, long_window)
        df_stationary = self.generate_buy_sell_signals(df_stationary)
        self.plot_signals_on_original_data(df_original, df_stationary, stock_name, short_window, long_window)