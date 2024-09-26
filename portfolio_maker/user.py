class User:
    def __init__(self, db):
        self.db = db

    def create_user(self):
        while True:
            user_id = input("Enter a unique user ID: ").strip()
            user_name = input("Enter your name: ").strip()

            # Check if the user_id already exists
            if self.user_exists(user_id):
                print(f"User ID '{user_id}' already exists. Please choose a different ID.")
            else:
                # Insert new user into the database
                query = 'INSERT INTO users (user_id, user_name) VALUES (%s, %s)'
                self.db.execute_query(query, (user_id, user_name))
                print(f"User '{user_name}' with ID '{user_id}' created successfully.")
                return user_id

    def get_user(self):
        user_id = input("Enter your user ID: ").strip()
        if self.user_exists(user_id):
            return user_id
        else:
            print(f"User ID '{user_id}' does not exist.")
            return None

    def user_exists(self, user_id):
        query = 'SELECT user_id FROM users WHERE user_id = %s'
        result = self.db.fetch_query(query, (user_id,))
        return len(result) > 0

    def get_user_name(self, user_id):
        query = 'SELECT user_name FROM users WHERE user_id = %s'
        result = self.db.fetch_query(query, (user_id,))
        if result:
            return result[0][0]  # Return the user_name
        else:
            return None

    def delete_user(self, user_id):
        try:
            # Delete related stock data first
            delete_stock_data_query = '''
                DELETE FROM stock_data
                WHERE ticker IN (
                    SELECT ticker FROM portfolio_stocks
                    WHERE portfolio_id IN (
                        SELECT portfolio_id FROM portfolios WHERE user_id = %s
                    )
                )
            '''
            self.db.execute_query(delete_stock_data_query, (user_id,))

            # Delete related records in the portfolio_stocks table
            delete_portfolio_stocks_query = '''
                DELETE FROM portfolio_stocks
                WHERE portfolio_id IN (
                    SELECT portfolio_id FROM portfolios WHERE user_id = %s
                )
            '''
            self.db.execute_query(delete_portfolio_stocks_query, (user_id,))

            # Delete related records in the portfolios table
            delete_portfolios_query = 'DELETE FROM portfolios WHERE user_id = %s'
            self.db.execute_query(delete_portfolios_query, (user_id,))

            # Finally, delete the user from the users table
            delete_user_query = 'DELETE FROM users WHERE user_id = %s'
            self.db.execute_query(delete_user_query, (user_id,))

            print(f"User '{user_id}' and all associated data have been successfully deleted.")
        except Exception as e:
            print(f"An error occurred while deleting the user: {e}")