import os
import pandas as pd
from datetime import datetime

class Portfolio:
    def __init__(self, db):
        self.db = db

    def create_portfolio(self, user_id):
        while True:
            name = input("Enter the name of the new portfolio (or type 'exit' to cancel): ").strip()
            if name.lower() == 'exit':
                print("Exiting portfolio creation.")
                return None

            creation_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            try:
                # Insert new portfolio into the database
                query = 'INSERT INTO portfolios \
                    (user_id, name, creation_date) VALUES (%s, %s, %s)'
                self.db.execute_query(query, (user_id, name, creation_date))
                print(f"Portfolio '{name}' created successfully for user ID '{user_id}'.")

                # Retrieve the portfolio ID of the newly created portfolio
                portfolio_id_query = 'SELECT portfolio_id FROM portfolios \
                    WHERE user_id = %s AND name = %s'
                portfolio_id = self.db.fetch_query(portfolio_id_query,
                                                   (user_id, name)
                                                   )

                if portfolio_id:
                    return portfolio_id[0][0]  # Return the portfolio ID
                else:
                    print("Failed to retrieve the portfolio ID.")
                    return None
            except Exception as e:
                print(f"An error occurred while creating the portfolio: {e}")
                return None

    def manage_existing_portfolio(self, user_id, user_name, stock_data_manager):
        while True:
            # Display portfolios for the user
            portfolios = self.display_portfolios(user_id)
            if not portfolios:
                return

            portfolio_id = input("\nEnter the portfolio ID you want to access (or type 'exit' to go back): ").strip()
            if portfolio_id.lower() == 'exit':
                print("Exiting to portfolio menu.")
                return

            try:
                portfolio_id = int(portfolio_id)
                # Check if the entered portfolio ID exists for this user
                portfolio_check_query = 'SELECT portfolio_id, name FROM portfolios WHERE user_id = %s AND portfolio_id = %s'
                portfolio_exists = self.db.fetch_query(portfolio_check_query, (user_id, portfolio_id))
                if not portfolio_exists:
                    print(f"Portfolio ID {portfolio_id} does not exist for user ID '{user_id}'.")
                    continue

                portfolio_name = portfolio_exists[0][1]

                while True:
                    print(f"\n--- Managing Portfolio ID {portfolio_id} ({portfolio_name}) ---")
                    print("1. Add stock to the portfolio")
                    print("2. Delete stock data from the portfolio")
                    print("3. Display all stock data")
                    print("4. Show portfolio summary")
                    print("5. View stock prices and metrics")
                    print("6. Export portfolio data to CSV")
                    print("7. Switch to another portfolio")
                    print("8. Go back")
                    choice = input("Enter your choice: ").strip().lower()

                    if choice == '1':
                        stock_data_manager.add_stock_data(portfolio_id)
                    elif choice == '2':
                        stock_name = input("Enter the stock ticker to delete (or type 'exit' to go back): ").upper()
                        if stock_name.lower() == 'exit':
                            continue
                        stock_data_manager.delete_stock_data(portfolio_id, stock_name)
                    elif choice == '3':
                        stock_data_manager.display_portfolio_data(portfolio_id)
                    elif choice == '4':
                        self.show_portfolio_summary(portfolio_id)
                    elif choice == '5':
                        stock_data_manager.view_stock_prices_and_metrics(portfolio_id)
                    elif choice == '6':
                        # Export portfolio data to CSV
                        self.export_portfolio_to_csv(user_id, user_name, portfolio_id, portfolio_name)
                    elif choice == '7':
                        break
                    elif choice == '8' or choice == 'exit':
                        print("Going back to portfolio menu.")
                        return
                    else:
                        print("Invalid choice. Please try again.")
            except ValueError:
                print("Invalid portfolio ID. Please try again.")

    def show_portfolio_summary(self, portfolio_id):
        try:
            # Get portfolio details
            portfolio_query = 'SELECT portfolio_id, name, creation_date FROM portfolios WHERE portfolio_id = %s'
            portfolio = self.db.fetch_query(portfolio_query, (portfolio_id,))
            
            if not portfolio:
                print(f"No portfolio found with ID {portfolio_id}.")
                return

            portfolio_id, name, creation_date = portfolio[0]

            # Get the list of tickers associated with the portfolio
            stock_query = 'SELECT ticker FROM portfolio_stocks WHERE portfolio_id = %s'
            stocks = self.db.fetch_query(stock_query, (portfolio_id,))
            stock_list = [stock[0] for stock in stocks]

            # Display the portfolio summary
            print(f"\nPortfolio ID: {portfolio_id}, Name: {name}, Created On: {creation_date}")
            print(f"Stocks: {', '.join(stock_list) if stock_list else 'No stocks in this portfolio.'}")
        
        except Exception as e:
            print(f"An error occurred while retrieving the portfolio summary: {e}")

    def display_portfolios(self, user_id):
        try:
            query = 'SELECT * FROM portfolios WHERE user_id = %s'
            portfolios = self.db.fetch_query(query, (user_id,))

            if not portfolios:
                print(f"No portfolios found for user ID '{user_id}'.")
                return None

            print(f"\nPortfolios found for user ID '{user_id}':")
            for portfolio in portfolios:
                print(f"Portfolio ID: {portfolio[0]}, Name: {portfolio[2]}, Created On: {portfolio[3]}")
                stock_query = 'SELECT ticker FROM \
                    portfolio_stocks WHERE portfolio_id = %s'
                stocks = self.db.fetch_query(stock_query, (portfolio[0],))
                stock_list = [stock[0] for stock in stocks]
                print(f"Stocks: {', '.join(stock_list)}")

            return portfolios
        except Exception as e:
            print(f"An error occurred while displaying portfolios: {e}")
            return None

    def export_portfolio_to_csv(self, user_id, user_name, portfolio_id, portfolio_name):
        try:
            # Fetch the portfolio creation date
            portfolio_query = 'SELECT creation_date FROM portfolios WHERE portfolio_id = %s'
            portfolio = self.db.fetch_query(portfolio_query, (portfolio_id,))
            if not portfolio:
                print(f"No portfolio found with ID {portfolio_id}.")
                return

            creation_date = portfolio[0][0].strftime('%Y-%m-%d')  # Format the creation date

            # Fetch stock data for the portfolio, sorted by ticker and date
            stock_query = '''
                SELECT date, ticker, adj_close, data_added_on
                FROM stock_data 
                WHERE ticker IN (
                    SELECT ticker FROM portfolio_stocks WHERE portfolio_id = %s
                )
                ORDER BY ticker, date
            '''
            stock_data = self.db.fetch_query(stock_query, (portfolio_id,))
            if not stock_data:
                print(f"No stock data available for portfolio ID {portfolio_id}.")
                return

            # Convert the result into a pandas DataFrame
            df = pd.DataFrame(stock_data, columns=['Date', 'Ticker', 'Adj Close', 'Data Added On'])

            # Create the directory structure: exported_data/{user_id}_{user_name}/{portfolio_name_creation_date}
            base_dir = os.path.join('exported_data', f'{user_id}_{user_name}', f'{portfolio_name}_{creation_date}')
            os.makedirs(base_dir, exist_ok=True)  # Create the folder if it doesn't exist

            # Get today's date and time for the file name
            now = datetime.now()
            todays_date = now.strftime('%Y-%m-%d')  # Get today's date
            current_time = now.strftime('%H-%M-%S')  # Get the current time

            # Generate the CSV file name: portfolio_name_todaysdate_currenttime.csv
            csv_filename = f'{portfolio_name}_{todays_date}_{current_time}.csv'
            csv_filepath = os.path.join(base_dir, csv_filename)

            # Export the DataFrame to CSV
            df.to_csv(csv_filepath, index=False)

            print(f"Portfolio data exported successfully to {csv_filepath}.")

        except Exception as e:
            print(f"An error occurred while exporting the portfolio: {e}")

