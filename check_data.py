from sqlalchemy import create_engine, text

# Define the SQLite database file
DATABASE_URL = "sqlite:///instance/steel_production.db"

# Create the database engine
engine = create_engine(DATABASE_URL)

# Function to print all available tables and their data
def print_all_tables_and_data():
    with engine.connect() as connection:
        # Query to get the list of tables
        tables_result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        
        # Fetch all table names
        tables = [row[0] for row in tables_result]
        
        print("Available tables:")
        for table in tables:
            print(f"- {table}")
            # Query to select all data from the table
            result = connection.execute(text(f"SELECT * FROM {table}"))
            
            # Print the results for each table
            for row in result:
                print(row)
            print()  # Add a newline for better readability

# Call the function to print tables and data
print_all_tables_and_data()
