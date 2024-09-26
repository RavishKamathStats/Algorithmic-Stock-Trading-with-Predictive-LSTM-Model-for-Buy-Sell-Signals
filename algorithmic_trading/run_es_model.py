from portfolio_maker.database import Database
from algorithmic_trading.models.es_model import ExponentialSmoothingModel


def get_user_id(db):
    while True:
        user_id = input("Enter your user ID (or type 'exit' to quit): ").strip()
        if user_id.lower() == "exit":
            return None

        # Check if the user ID exists in the database
        query = "SELECT user_id FROM users WHERE user_id = %s"
        result = db.fetch_query(query, (user_id,))

        if result:
            return user_id
        else:
            print(
                "Invalid user ID. Please enter a valid user ID or, if you're a new user, run the 'run_stock_trading.py' script to create a portfolio."
            )


def check_user_portfolios(db, user_id):
    query = "SELECT portfolio_id, name FROM portfolios WHERE user_id = %s"
    portfolios = db.fetch_query(query, (user_id,))

    if not portfolios:
        print(
            f"No portfolios found for user ID '{user_id}'. Please run 'run_stock_trading.py' to create a portfolio."
        )
        return None
    else:
        print(f"\nPortfolios for User ID '{user_id}':")
        for portfolio in portfolios:
            portfolio_id, portfolio_name = portfolio
            print(f"Portfolio ID: {portfolio_id}, Name: {portfolio_name}")
        return portfolios


def select_portfolio(portfolios):
    while True:
        portfolio_id = input(
            "\nEnter the portfolio ID to analyze (or type 'exit' to quit): "
        ).strip()
        if portfolio_id.lower() == "exit":
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
            input(f"Enter the stock ticker to analyze (or type 'exit' to quit): ")
            .strip()
            .upper()
        )
        if ticker.lower() == "exit":
            return None
        if ticker in stock_list:
            return ticker
        else:
            print("Invalid ticker. Please enter a valid ticker from the list.")


def get_seasonal_values():
    while True:
        seasonal = (
            input(
                "Enter the seasonal type (additive/multiplicative) or 'none' for no seasonality: "
            )
            .strip()
            .lower()
        )
        if seasonal in ["additive", "multiplicative", "none"]:
            break
        else:
            print(
                "Invalid input. Please enter 'additive', 'multiplicative', or 'none'."
            )
    if seasonal != "none":
        while True:
            try:
                seasonal_periods = int(
                    input(
                        "Enter the seasonal period (e.g., 12 for yearly seasonality): "
                    ).strip()
                )
                return seasonal, seasonal_periods
            except ValueError:
                print("Please enter a valid numeric value for the seasonal period.")
    return None, None


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
        es_model = ExponentialSmoothingModel(db)
        stock_data = es_model.get_stock_data(portfolio_id, ticker)
        es_model.plot_original_data(stock_data, ticker)
        trend_detected, d = es_model.detect_trend(stock_data)
        es_model.plot_acf_and_save(trend_detected, ticker)
        seasonal, seasonal_periods = get_seasonal_values()
        es_model.run_model(
            portfolio_id, ticker, seasonal=seasonal, seasonal_periods=seasonal_periods
        )
        next_action = (
            input("Do you want to analyze another stock? (yes/exit): ").strip().lower()
        )
        if next_action == "exit":
            print("Exiting the system.")
            return


if __name__ == "__main__":
    main()
