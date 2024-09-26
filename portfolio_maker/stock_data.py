import yfinance as yf
import pandas as pd
from datetime import datetime

class StockData:
    def __init__(self, db):
        self.db = db

    def add_stock_data(self, portfolio_id):
        # Get stock tickers from the user (comma-separated list)
        tickers = input("Enter the stock tickers (comma-separated): ").strip().upper().split(',')

        # Strip any extra whitespace from each ticker
        tickers = [ticker.strip() for ticker in tickers if ticker.strip()]

        # Ask user to select a time period from the available options
        time_options = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd']
        print(f"\nSelect a time period for the stocks:")
        for i, option in enumerate(time_options, 1):
            print(f"{i}. {option}")
        time_choice = int(input("Enter the number corresponding to your time period: ").strip()) - 1
        if time_choice < 0 or time_choice >= len(time_options):
            print("Invalid time period selected. Exiting.")
            return
        time_period = time_options[time_choice]

        # Ask user to select an interval range from the available options
        interval_options = ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo']
        print(f"\nSelect an interval range for the stocks:")
        for i, option in enumerate(interval_options, 1):
            print(f"{i}. {option}")
        interval_choice = int(input("Enter the number corresponding to your interval range: ").strip()) - 1
        if interval_choice < 0 or interval_choice >= len(interval_options):
            print("Invalid interval range selected. Exiting.")
            return
        interval = interval_options[interval_choice]

        for ticker in tickers:
            try:
                # Fetch the stock data using yfinance for the current ticker
                stock_data = yf.download(ticker, period=time_period, interval=interval)

                # Check if any data was returned
                if stock_data.empty:
                    print(f"No data found for {ticker} with the selected time period and interval.")
                    continue

                # Add a new column for the date when the data is added
                stock_data['Data_Added_On'] = datetime.now()

                # Step 1: Check if the ticker is already in the portfolio_stocks table
                ticker_exists_query = '''
                    SELECT COUNT(*) FROM portfolio_stocks WHERE portfolio_id = %s AND ticker = %s
                '''
                result = self.db.fetch_query(ticker_exists_query, (portfolio_id, ticker))
                
                if result[0][0] == 0:
                    # If the ticker doesn't exist in the portfolio_stocks table, insert it
                    insert_ticker_query = '''
                        INSERT INTO portfolio_stocks (portfolio_id, ticker)
                        VALUES (%s, %s)
                    '''
                    self.db.execute_query(insert_ticker_query, (portfolio_id, ticker))
                    print(f"Ticker '{ticker}' added to portfolio ID {portfolio_id}.")

                # Step 2: Insert stock data into the stock_data table
                for date, row in stock_data.iterrows():
                    adj_close = row['Adj Close']
                    data_added_on = row['Data_Added_On']

                    # Convert pandas.Timestamp to Python datetime for 'date' field
                    if isinstance(date, pd.Timestamp):
                        date = date.to_pydatetime()  # Convert to Python datetime
                    
                    # Ensure data_added_on is a Python datetime object
                    if isinstance(data_added_on, pd.Timestamp):
                        data_added_on = data_added_on.to_pydatetime()  # Convert to Python datetime
                    
                    if pd.notna(adj_close):  # Make sure to only insert rows with valid data
                        self.db.execute_query(
                            'INSERT INTO stock_data (date, ticker, adj_close, data_added_on) VALUES (%s, %s, %s, %s)',
                            (date, ticker, adj_close, data_added_on)
                        )
                
                print(f"Stock data for {ticker} added successfully for {time_period} with interval {interval}.")
            
            except Exception as e:
                print(f"An error occurred while adding stock data for {ticker}: {e}")

    def delete_stock_data(self, portfolio_id, ticker):
        # Delete the stock data for the given ticker
        try:
            # Subquery to fetch the dates to be deleted for the given ticker and portfolio_id
            delete_query = '''
                DELETE FROM stock_data
                WHERE ticker = %s AND date IN (
                    SELECT date FROM (
                        SELECT sd.date
                        FROM stock_data sd
                        JOIN portfolio_stocks ps ON sd.ticker = ps.ticker
                        WHERE ps.portfolio_id = %s AND sd.ticker = %s
                    ) AS temp_subquery
                )
            '''
            self.db.execute_query(delete_query, (ticker, portfolio_id, ticker))
            print(f"All data for stock '{ticker}' in portfolio {portfolio_id} has been deleted.")

            # Step 2: Check if any stock data remains for the given ticker in the portfolio
            check_query = '''
                SELECT COUNT(*) FROM stock_data 
                WHERE ticker = %s AND date IN (
                    SELECT date FROM portfolio_stocks WHERE portfolio_id = %s
                )
            '''
            result = self.db.fetch_query(check_query, (ticker, portfolio_id))

            # If no stock data remains, delete the ticker from portfolio_stocks
            if result[0][0] == 0:
                delete_portfolio_stock_query = '''
                    DELETE FROM portfolio_stocks
                    WHERE portfolio_id = %s AND ticker = %s
                '''
                self.db.execute_query(delete_portfolio_stock_query, (portfolio_id, ticker))
                print(f"Ticker '{ticker}' removed from portfolio {portfolio_id}.")

        except Exception as e:
            print(f"An error occurred while deleting stock data for {ticker}: {e}")

    def display_portfolio_data(self, portfolio_id):
        try:
            # Fetch stock data for the portfolio from the database
            query = '''
                SELECT date, ticker, adj_close, data_added_on 
                FROM stock_data 
                WHERE ticker IN (
                    SELECT ticker FROM portfolio_stocks WHERE portfolio_id = %s
                )
                ORDER BY ticker, date
            '''
            result = self.db.fetch_query(query, (portfolio_id,))
            
            if result:
                print(f"\nStock Data for Portfolio ID {portfolio_id}:")
                for row in result:
                    date, ticker, adj_close, data_added_on = row
                    print(f"Date & Time: {date}, Ticker: {ticker}, Adj Close: {adj_close}, Data Added On: {data_added_on}")
            else:
                print(f"No data available for portfolio ID {portfolio_id}.")
        
        except Exception as e:
            print(f"An error occurred while fetching portfolio data: {e}")

    def view_stock_prices_and_metrics(self, portfolio_id):
        try:
            # Fetch stock data for the portfolio from the database, sorted by ticker and date
            query = '''
                SELECT date, ticker, adj_close
                FROM stock_data 
                WHERE ticker IN (
                    SELECT ticker FROM portfolio_stocks WHERE portfolio_id = %s
                )
                ORDER BY ticker, date
            '''
            result = self.db.fetch_query(query, (portfolio_id,))
            
            if not result:
                print(f"No stock data available for portfolio ID {portfolio_id}.")
                return

            # Convert result to DataFrame for easier processing
            df = pd.DataFrame(result, columns=['Date', 'Ticker', 'Adj Close'])

            # Group by ticker and calculate basic metrics (e.g., volatility, mean price)
            grouped = df.groupby('Ticker').agg(
                volatility=('Adj Close', lambda x: x.pct_change().std() * 100),
                mean_price=('Adj Close', 'mean')
            )

            # Display the last 5 prices for each stock and the calculated metrics
            print(f"\nStock Metrics for Portfolio ID {portfolio_id}:")
            for ticker, data in grouped.iterrows():
                print(f"\nTicker: {ticker}")
                print(f"Volatility: {data['volatility']:.2f}%")
                print(f"Mean Adjusted Close Price: {data['mean_price']:.2f}")
                
                # Display the last 5 prices for each stock
                ticker_data = df[df['Ticker'] == ticker].tail(5)
                print("Last 5 Prices:")
                print(ticker_data[['Date', 'Adj Close']])
        
        except Exception as e:
            print(f"An error occurred while fetching stock metrics: {e}")