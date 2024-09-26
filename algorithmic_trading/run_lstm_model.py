from portfolio_maker.database import Database
from algorithmic_trading.models.lstm_model import LSTMModel


def get_user_id(db):
    while True:
        user_id = input("Enter your user ID (or type 'exit' to quit): ").strip()
        if user_id.lower() == "exit":
            return None
        query = "SELECT user_id FROM users WHERE user_id = %s"
        result = db.fetch_query(query, (user_id,))
        if result:
            return user_id
        else:
            print(
                "Invalid user ID. Please enter a valid user ID or, if you're a new user, run the 'run_stock_trading.py' script to create a portfolio."
            )


def check_user_portfolios(db, user_id):
    query = (
        "SELECT portfolio_id, name, creation_date FROM portfolios WHERE user_id = %s"
    )
    portfolios = db.fetch_query(query, (user_id,))
    if not portfolios:
        print(
            f"No portfolios found for user ID '{user_id}'. Please run 'run_stock_trading.py' to create a portfolio."
        )
        return None
    else:
        print(f"\nPortfolios for User ID '{user_id}':")
        for portfolio in portfolios:
            portfolio_id, portfolio_name, creation_date = portfolio
            stock_query = "SELECT ticker FROM portfolio_stocks WHERE portfolio_id = %s"
            stocks = db.fetch_query(stock_query, (portfolio_id,))
            stock_list = [stock[0] for stock in stocks]
            print(f"Portfolio ID: {portfolio_id}, Name: {portfolio_name}")
            print(f"Created On: {creation_date}")
            print(
                f"Stocks: {', '.join(stock_list) if stock_list else 'No stocks in this portfolio.'}"
            )
            print("-" * 40)

        return portfolios


def select_portfolio(portfolios):
    while True:
        portfolio_id = (
            input("\nEnter the portfolio ID to analyze (or type 'exit' to quit): ")
            .strip()
            .lower()
        )
        if portfolio_id == "exit":
            return None
        try:
            portfolio_id = int(portfolio_id)
            if any(portfolio_id == portfolio[0] for portfolio in portfolios):
                return portfolio_id
            else:
                print("Invalid portfolio ID. Please enter a valid portfolio ID.")
        except ValueError:
            print("Please enter a numeric portfolio ID.")


def select_stock(portfolio_id, db):
    query = "SELECT ticker FROM portfolio_stocks WHERE portfolio_id = %s"
    stocks = db.fetch_query(query, (portfolio_id,))
    stock_list = [stock[0] for stock in stocks]

    if not stock_list:
        print(f"No stocks available in portfolio {portfolio_id}.")
        return None
    print(f"\nAvailable stocks in Portfolio {portfolio_id}: {', '.join(stock_list)}")
    while True:
        ticker = (
            input(f"\nEnter the stock ticker to analyze (or type 'exit' to quit): ")
            .strip()
            .upper()
        )
        if ticker.lower() == "exit":
            return None

        if ticker in stock_list:
            return ticker
        else:
            print("Invalid ticker. Please enter a valid ticker from the portfolio.")


def main():
    db = Database(
        user="ravish1996",
        password="newpassword",
        host="localhost",
        database="stockTrading",
    )
    user_id = get_user_id(db)
    if not user_id:
        print("Exiting the system.")
        return
    portfolios = check_user_portfolios(db, user_id)
    if not portfolios:
        return
    portfolio_id = select_portfolio(portfolios)
    if not portfolio_id:
        print("Exiting the system.")
        return
    while True:
        ticker = select_stock(portfolio_id, db)
        if not ticker:
            print("Exiting the system.")
            return
        # Predefined LSTM-specific parameters for Tech stocks
        time_steps = 60
        epochs = 50
        batch_size = 32
        model = LSTMModel(db)
        df = model.run_lstm(
            portfolio_id,
            ticker,
            time_steps=time_steps,
            epochs=epochs,
            batch_size=batch_size,
        )
        print("\nBuy/Sell signals generated and plotted for the selected stock.")
        next_action = (
            input("Do you want to analyze another stock? (yes, exit): ").strip().lower()
        )
        if next_action == "exit":
            print("Exiting the system.")
            return


if __name__ == "__main__":
    main()
