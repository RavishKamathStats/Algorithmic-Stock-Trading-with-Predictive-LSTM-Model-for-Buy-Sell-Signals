import mysql.connector

class Database:
    def __init__(self, user, password, host, database=None):
        self.config = {
            'user': user,
            'password': password,
            'host': host,
            'database': database,  # Optional, can be None when creating a database
            'connection_timeout': 30  # Set a timeout for the connection
        }
        self.conn = None

    def connect(self):
        if not self.conn or not self.conn.is_connected():
            self.conn = mysql.connector.connect(**self.config)
        return self.conn

    def create_database(self, database_name):
        try:
            # Connect to MySQL server (without specifying a database)
            conn = mysql.connector.connect(
                user=self.config['user'],
                password=self.config['password'],
                host=self.config['host']
            )
            cursor = conn.cursor()
            
            # Create the database
            cursor.execute(f'CREATE DATABASE IF NOT EXISTS {database_name}')
            print(f"Database '{database_name}' created successfully.")
            
            cursor.close()
            conn.close()
        except mysql.connector.Error as e:
            print(f"Error creating database: {e}")

    def execute_query(self, query, params=None):
        conn = self.connect()
        with conn.cursor() as cursor:
            try:
                cursor.execute(query, params)
                conn.commit()
            except Exception as e:
                print(f"An error occurred during query execution: {e}")

    def fetch_query(self, query, params=None):
        conn = self.connect()
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchall()
        return result

    def close(self):
        if self.conn and self.conn.is_connected():
            self.conn.close()
            self.conn = None

    def create_tables(self):
        try:
            # Create `users` table
            print("Creating 'users' table...")
            self.execute_query('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id VARCHAR(50) PRIMARY KEY,
                    user_name VARCHAR(255) NOT NULL
                )
            ''')

            # Create `portfolios` table with `user_id` foreign key and ON DELETE CASCADE
            print("Creating 'portfolios' table...")
            self.execute_query('''
                CREATE TABLE IF NOT EXISTS portfolios (
                    portfolio_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id VARCHAR(50),
                    name VARCHAR(255) NOT NULL,
                    creation_date DATETIME NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            ''')

            # Create `portfolio_stocks` table with ON DELETE CASCADE
            print("Creating 'portfolio_stocks' table...")
            self.execute_query('''
                CREATE TABLE IF NOT EXISTS portfolio_stocks (
                    portfolio_id INT,
                    ticker VARCHAR(10) NOT NULL,
                    FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id) ON DELETE CASCADE
                )
            ''')

            # Create `stock_data` table (No foreign keys here)
            print("Creating 'stock_data' table...")
            self.execute_query('''
                CREATE TABLE IF NOT EXISTS stock_data (
                    date DATETIME,
                    ticker VARCHAR(10),
                    adj_close FLOAT,
                    data_added_on DATETIME
                )
            ''')

            print("All tables created successfully.")
        except Exception as e:
            print(f"An error occurred while creating tables: {e}")

    def drop_tables(self):
        try:
            # Disable foreign key checks to allow dropping tables with foreign keys
            print("Disabling foreign key checks...")
            self.execute_query('SET FOREIGN_KEY_CHECKS = 0')

            # Drop tables in reverse order of creation to maintain foreign key integrity
            table_names = ['stock_data', 'portfolio_stocks', 'portfolios', 'users']
            for table in table_names:
                print(f"Dropping table: {table}...")
                try:
                    self.execute_query(f'DROP TABLE IF EXISTS {table}')
                    print(f"Table '{table}' dropped successfully.")
                except Exception as e:
                    print(f"An error occurred while dropping table '{table}': {e}")
            
            # Re-enable foreign key checks
            print("Re-enabling foreign key checks...")
            self.execute_query('SET FOREIGN_KEY_CHECKS = 1')
        except Exception as e:
            print(f"An error occurred while dropping tables: {e}")