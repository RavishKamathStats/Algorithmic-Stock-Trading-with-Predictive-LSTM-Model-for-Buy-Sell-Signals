import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout
import os
from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np

class LSTMModel:
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
        # Normalize the data
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(df['Adj Close'].values.reshape(-1, 1))

        X, y = [], []
        for i in range(time_steps, len(scaled_data)):
            X.append(scaled_data[i-time_steps:i, 0])
            y.append(scaled_data[i, 0])

        X, y = np.array(X), np.array(y)
        X = np.reshape(X, (X.shape[0], X.shape[1], 1))  # Reshape to LSTM input shape

        return X, y, scaler

    def build_lstm_model(self, input_shape):
        model = Sequential()
        model.add(LSTM(units=50, return_sequences=True, input_shape=(input_shape[1], 1)))
        model.add(Dropout(0.2))
        model.add(LSTM(units=50, return_sequences=False))
        model.add(Dropout(0.2))
        model.add(Dense(units=1))  # Output layer for regression (1 value)

        model.compile(optimizer='adam', loss='mean_squared_error')
        return model

    def train_lstm_model(self, model, X_train, y_train, epochs=10, batch_size=32):
        model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, verbose=1)
        return model

    def predict(self, model, X_test, scaler):
        predictions = model.predict(X_test)
        predictions = scaler.inverse_transform(predictions) 
        return predictions.flatten()  

    def plot_lstm_results(self, df, predictions, stock_name):
        """Plot the original data, LSTM predicted values, and Buy/Sell signals."""
        plt.figure(figsize=(12, 6))
        plt.plot(df['Adj Close'], label=f'{stock_name} Actual Prices', alpha=0.6)
        plt.plot(df.index, predictions, label=f'{stock_name} LSTM Predictions', alpha=0.75, color='orange')
        buy_signals = df['Buy_Signal'].dropna()
        sell_signals = df['Sell_Signal'].dropna()
        plt.scatter(buy_signals.index, buy_signals, label='Buy Signal', marker='^', color='green', alpha=1)
        plt.scatter(sell_signals.index, sell_signals, label='Sell Signal', marker='v', color='red', alpha=1)
        plt.title(f'{stock_name} LSTM Predictions vs Actual Prices with Buy/Sell Signals')
        plt.xlabel('Date')
        plt.ylabel('Adjusted Close Price')
        plt.legend()

        output_dir = os.path.join("plots", "LSTM_model")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        output_file = os.path.join(output_dir, f"{stock_name}_lstm_predictions_with_signals.png")
        plt.savefig(output_file)
        print(f"Plot saved as {output_file}")
        plt.close()

    def generate_buy_sell_signals(self, df, predictions, threshold=0.1):
        """Generate buy and sell signals based on predicted vs actual prices with a reduced threshold."""
        predictions = predictions.flatten()  # Ensure predictions is 1D
        df = df.iloc[-len(predictions):].copy()
        df['Buy_Signal'] = np.where((predictions - df['Adj Close']) > threshold, df['Adj Close'], np.nan)
        df['Sell_Signal'] = np.where((df['Adj Close'] - predictions) > threshold, df['Adj Close'], np.nan)
        return df

    def run_lstm(self, portfolio_id, stock_name, time_steps=60, epochs=10, batch_size=32):
        """Run LSTM model, plot results, evaluate, and generate buy/sell signals."""
        df = self.get_stock_data(portfolio_id, stock_name)
        X, y, scaler = self.prepare_data(df, time_steps)
        train_size = int(len(X) * 0.8)
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]
        model = self.build_lstm_model(X_train.shape)
        model = self.train_lstm_model(model, X_train, y_train, epochs=epochs, batch_size=batch_size)
        predictions = self.predict(model, X_test, scaler)
        mae = mean_absolute_error(y_test, predictions)
        rmse = np.sqrt(mean_squared_error(y_test, predictions))
        print(f"Mean Absolute Error (MAE): {mae}")
        print(f"Root Mean Squared Error (RMSE): {rmse}")
        df = df.iloc[-len(predictions):]
        df = self.generate_buy_sell_signals(df, predictions)
        self.plot_lstm_results(df, predictions, stock_name)

        return df