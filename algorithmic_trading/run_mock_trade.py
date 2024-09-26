import os
import csv
from datetime import datetime
from portfolio_maker.database import Database
from algorithmic_trading.models.lstm_trading_env import LSTMTradingEnv


def get_user_id(db):
    while True:
        user_id = input("Enter your user ID (or type 'exit' to quit): ").strip()
        if user_id.lower() == "exit":
            return None, None
        query = "SELECT user_id, user_name FROM users WHERE user_id = %s"
        result = db.fetch_query(query, (user_id,))
        if result:
            return user_id, result[0][1]
        else:
            print(
                "Invalid user ID. Please enter a valid user ID or, if you're a new user, run the 'run_stock_trading.py' script to create a portfolio."
            )


def select_portfolio(db, user_id):
    query = "SELECT portfolio_id, name FROM portfolios WHERE user_id = %s"
    portfolios = db.fetch_query(query, (user_id,))
    if not portfolios:
        print(
            f"No portfolios found for user ID '{user_id}'. Please run 'run_stock_trading.py' to create a portfolio."
        )
        return None, None
    print(f"\nPortfolios for User ID '{user_id}':")
    for portfolio in portfolios:
        print(f"Portfolio ID: {portfolio[0]}, Name: {portfolio[1]}")
    while True:
        portfolio_id = input(
            "Enter the portfolio ID to use for trading (or type 'exit' to quit): "
        ).strip()
        if portfolio_id.lower() == "exit":
            return None, None
        try:
            portfolio_id = int(portfolio_id)
            for portfolio in portfolios:
                if portfolio_id == portfolio[0]:
                    return portfolio_id, portfolio[1]
            print("Invalid portfolio ID. Please enter a valid ID.")
        except ValueError:
            print("Invalid input. Please enter a valid numeric ID.")


def select_stock(db, portfolio_id):
    query = "SELECT ticker FROM portfolio_stocks WHERE portfolio_id = %s"
    stocks = db.fetch_query(query, (portfolio_id,))
    stock_list = [stock[0] for stock in stocks]
    if not stock_list:
        print(f"No stocks available in portfolio {portfolio_id}.")
        return None
    print("\nAvailable stocks in the portfolio:")
    print(", ".join(stock_list))
    while True:
        ticker = (
            input("Enter the stock ticker to trade (or type 'exit' to quit): ")
            .strip()
            .upper()
        )
        if ticker.lower() == "exit":
            return None
        if ticker in stock_list:
            return ticker
        else:
            print("Invalid ticker. Please enter a valid ticker from the portfolio.")


def get_trading_duration():
    while True:
        print("\nAvailable trading durations:")
        print("1. 1 Week")
        print("2. 1 Month")
        print("3. 3 Months")
        print("4. 6 Months")
        print("5. 1 Year")
        duration = input("Select a trading duration (1-5): ").strip()
        if duration == "1":
            return "1w", 5  # 1 week = 5 trading days
        elif duration == "2":
            return "1m", 21  # 1 month = 21 trading days
        elif duration == "3":
            return "3m", 63  # 3 months = 63 trading days
        elif duration == "4":
            return "6m", 126  # 6 months = 126 trading days
        elif duration == "5":
            return "1y", 252  # 1 year = 252 trading days
        else:
            print("Invalid selection. Please choose a valid option.")


def get_shares_per_trade():
    while True:
        try:
            shares = int(input("Enter the number of shares per trade: ").strip())
            return shares
        except ValueError:
            print("Invalid input. Please enter a valid numeric value.")


def export_trades_to_csv(
    trade_log, user_id, username, portfolio_name, stock_name, duration
):
    base_dir = os.path.join("mock_trades", f"{user_id}_{username}", portfolio_name)
    os.makedirs(base_dir, exist_ok=True)
    date_created = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"{stock_name}_{duration}_{date_created}.csv"
    file_path = os.path.join(base_dir, file_name)
    headers = [
        "Date",
        "Close Price",
        "Action",
        "Shares Held",
        "Shares Traded",
        "Shares Used ($)",
        "Portfolio Value ($)",
        "Cash Remaining ($)",
    ]
    with open(file_path, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(trade_log)

    print(f"Trade log successfully exported to {file_path}")


def main():
    db = Database(
        user="ravish1996",
        password="newpassword",
        host="localhost",
        database="stockTrading",
    )
    user_id, username = get_user_id(db)
    if not user_id:
        print("Exiting the system.")
        return
    portfolio_id, portfolio_name = select_portfolio(db, user_id)
    if not portfolio_id:
        print("Exiting the system.")
        return
    trading_env = LSTMTradingEnv(db)
    initial_investment = None

    while True:
        stock_ticker = select_stock(db, portfolio_id)
        if not stock_ticker:
            print("Exiting the system.")
            return
        duration_type, trading_days = get_trading_duration()
        if initial_investment is None:
            initial_investment = float(input("Enter the initial investment amount: $"))
        shares_per_trade = get_shares_per_trade()
        trade_log, portfolio_values, total_profit = (
            trading_env.run_lstm_trading_simulation(
                portfolio_id=portfolio_id,
                ticker=stock_ticker,
                time_steps=60,
                epochs=10,
                batch_size=32,
                initial_investment=initial_investment,
                shares_per_trade=shares_per_trade,
            )
        )
        export_csv = (
            input("Do you want to export the trade log to a CSV file? (y/n): ")
            .strip()
            .lower()
        )
        if export_csv == "y":
            export_trades_to_csv(
                trade_log,
                user_id,
                username,
                portfolio_name,
                stock_ticker,
                duration_type,
            )
        initial_investment = portfolio_values[-1]
        next_action = (
            input(
                "Do you want to trade again or exit? (Type 'trade' to trade again or 'exit' to quit): "
            )
            .strip()
            .lower()
        )
        if next_action == "exit":
            print("Exiting the system.")
            return


if __name__ == "__main__":
    main()
