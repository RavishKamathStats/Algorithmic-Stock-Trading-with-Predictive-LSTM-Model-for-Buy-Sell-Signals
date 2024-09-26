import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout
from sklearn.metrics import mean_absolute_error, mean_squared_error
from tabulate import tabulate

class LSTMTradingEnv:
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

    def prepare_data(self, df, time_steps=60):
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(df['Adj Close'].values.reshape(-1, 1))
        X, y = [], []
        for i in range(time_steps, len(scaled_data)):
            X.append(scaled_data[i-time_steps:i, 0])
            y.append(scaled_data[i, 0])
        X, y = np.array(X), np.array(y)
        X = np.reshape(X, (X.shape[0], X.shape[1], 1))  

        return X, y, scaler

    def build_lstm_model(self, input_shape):
        """Build and compile the LSTM model."""
        model = Sequential()
        model.add(LSTM(units=50, return_sequences=True, input_shape=(input_shape[1], 1)))
        model.add(Dropout(0.2))
        model.add(LSTM(units=50, return_sequences=False))
        model.add(Dropout(0.2))
        model.add(Dense(units=1))

        model.compile(optimizer='adam', loss='mean_squared_error')
        return model

    def train_lstm_model(self, model, X_train, y_train, epochs=10, batch_size=32):
        """Train the LSTM model."""
        model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, verbose=1)
        return model

    def predict(self, model, X_test, scaler):
        predictions = model.predict(X_test)
        predictions = scaler.inverse_transform(predictions)
        return predictions.flatten()

    def generate_lstm_signals(self, df, predictions, threshold=0.1):
        predictions = predictions.flatten()
        df = df.iloc[-len(predictions):].copy()
        df['Buy_Signal'] = np.where((predictions - df['Adj Close']) > threshold, df['Adj Close'], np.nan)
        df['Sell_Signal'] = np.where((df['Adj Close'] - predictions) > threshold, df['Adj Close'], np.nan)

        return df

    def simulate_trades(self, df, initial_investment=10000, shares_per_trade=10):
        cash = initial_investment
        shares_held = 0
        total_profit = 0
        portfolio_values = []
        trade_log = []

        for i in range(len(df)):
            price = df['Adj Close'].iloc[i]
            date = df.index[i]
            action = "Hold"
            shares_used = 0
            if not np.isnan(df['Buy_Signal'].iloc[i]) and cash >= price * shares_per_trade:
                shares_held += shares_per_trade
                shares_used = price * shares_per_trade
                cash -= shares_used
                action = "Buy"
                total_profit -= shares_used 
            elif not np.isnan(df['Sell_Signal'].iloc[i]) and shares_held >= shares_per_trade:
                shares_held -= shares_per_trade
                shares_used = price * shares_per_trade
                cash += shares_used
                action = "Sell"
                total_profit += shares_used 

            portfolio_value = cash + (shares_held * price)
            portfolio_values.append(portfolio_value)
            trade_log.append([date, round(price, 2), action, shares_held, shares_per_trade, round(shares_used, 2), round(portfolio_value, 2), round(cash, 2)])
        print("\nTrade Log:")
        headers = ["Date", "Close Price", "Action", "Shares Held", "Shares Traded", "Shares Used ($)", "Portfolio Value ($)", "Cash Remaining ($)"]
        print(tabulate(trade_log, headers=headers, tablefmt="grid"))

        return trade_log, portfolio_values, total_profit

    def calculate_performance_metrics(self, portfolio_values, total_profit, trading_days):
        total_return = (portfolio_values[-1] - portfolio_values[0]) / portfolio_values[0]
        annualized_return = ((1 + total_return) ** (252 / trading_days)) - 1

        returns = pd.Series(portfolio_values).pct_change().dropna()
        sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252)

        print(f"\nTotal Profit: {total_profit:.2f}")
        print(f"Total Portfolio Value: {portfolio_values[-1]:.2f}")
        print(f"Total Return of Investment: {total_return * 100:.2f}%")
        print(f"Annualized Returns: {annualized_return * 100:.2f}%")
        print(f"Sharpe Ratio: {sharpe_ratio:.2f}")

    def run_lstm_trading_simulation(self, portfolio_id, ticker, time_steps=60, epochs=10, batch_size=32, initial_investment=10000, shares_per_trade=10):
        df = self.get_stock_data(portfolio_id, ticker)
        X, y, scaler = self.prepare_data(df, time_steps)
        train_size = int(len(X) * 0.8)
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]
        model = self.build_lstm_model(X_train.shape)
        model = self.train_lstm_model(model, X_train, y_train, epochs=epochs, batch_size=batch_size)
        predictions = self.predict(model, X_test, scaler)
        df_signals = self.generate_lstm_signals(df, predictions)
        trade_log, portfolio_values, total_profit = self.simulate_trades(df_signals, initial_investment, shares_per_trade)
        self.calculate_performance_metrics(portfolio_values, total_profit, len(df_signals))
        return trade_log, portfolio_values, total_profit