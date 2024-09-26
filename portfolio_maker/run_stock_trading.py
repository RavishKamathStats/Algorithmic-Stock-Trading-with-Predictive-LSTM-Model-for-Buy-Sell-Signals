from database import Database
from portfolio import Portfolio
from stock_data import StockData
from user import User

def setup_database():
    db = Database(user='root', password='newpassword', host='localhost')
    db.create_database('stockTrading')
    db = Database(user='ravish1996', password='newpassword', host='localhost', database='stockTrading')
    db.create_tables()
    return db

def main():
    # Step 1: Set up the database and tables
    db = setup_database()
    
    # Initialize the user, portfolio, and stock data managers
    user_manager = User(db)
    portfolio_manager = Portfolio(db)
    stock_data_manager = StockData(db)
    
    # User registration or login
    user_id = None
    user_name = None  # Track the user's name
    while not user_id:
        print("\n--- User Menu ---")
        print("1. Create a new user")
        print("2. Log in with an existing user ID")
        print("Type 'exit' to exit the application.")
        choice = input("Enter your choice: ").strip().lower()
        if choice == '1':
            user_id = user_manager.create_user()
            user_name = user_manager.get_user_name(user_id)  # Get the user's name when creating a new user
        elif choice == '2':
            user_id = user_manager.get_user()
            if user_id:
                user_name = user_manager.get_user_name(user_id)  # Get the user's name when logging in
        elif choice == 'exit':
            print("Thank you for using our stock trading program\nExiting...")
            db.close()
            return
        else:
            print("Invalid choice. Please try again.")

    # Main menu for both new and existing users
    while True:
        print(f"\n--- Portfolio Menu (User: {user_id}, Name: {user_name}) ---")
        print("1. Create a new portfolio")
        print("2. View and manage an existing portfolio")
        print("3. Delete your account")
        print("4. Exit")
        choice = input("Enter your choice: ").strip().lower()

        if choice == '1':
            portfolio_id = portfolio_manager.create_portfolio(user_id)
            if portfolio_id:
                stock_data_manager.add_stock_data(portfolio_id)
        elif choice == '2':
            portfolio_manager.manage_existing_portfolio(user_id, user_name, stock_data_manager)  # Pass user_name here
        elif choice == '3':
            message = f"Are you sure you want to delete your account '{user_id}' and all its data? (yes/no): "
            confirm = input(message).strip().lower()
            if confirm == 'yes':
                user_manager.delete_user(user_id)
                print("Your account has been deleted. Exiting...")
                return
            else:
                print("Account deletion canceled.")
        elif choice == '4' or choice == 'exit':
            print("Thank you for using our stock trading program\nExiting...")
            break
        else:
            print("Invalid choice. Please try again.")
    db.close()

if __name__ == '__main__':
    main()