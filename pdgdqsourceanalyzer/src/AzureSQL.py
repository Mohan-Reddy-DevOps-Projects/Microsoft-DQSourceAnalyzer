from pydantic import BaseModel
import pyodbc
from azure.identity import DefaultAzureCredential
from typing import List, Dict

class AzureSQLRequest(BaseModel):
    server: str
    database: str

    def test_connection(server: str, database: str) -> Dict[str, str]:
        port = 1433

        try:
            # Obtain a token from MSI
            credential = DefaultAzureCredential()
            token = credential.get_token("https://database.windows.net/.default").token

            # Create a connection string
            connection_string = (
                f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"Authentication=ActiveDirectoryMsi;"
                f"Token={token};"
            )
            connection = pyodbc.connect(connection_string)
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            connection.close()

            return {"status": "success", "message": "Connection successful"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

class AzureSQLSchemaRequest(BaseModel):
    server: str
    database: str
    table: str

    def get_table_schema(server: str, database: str, table: str) -> Dict[str, List[Dict[str, str]]]:
        port = 1433 

        try:
            credential = DefaultAzureCredential()
            token = credential.get_token("https://database.windows.net/.default").token

            connection_string = (
                f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"Authentication=ActiveDirectoryMsi;"
                f"Token={token};"
            )
            connection = pyodbc.connect(connection_string)
            cursor = connection.cursor()
            query = f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}'"
            cursor.execute(query)

            columns = cursor.fetchall()
            schema_info = [{"column_name": row[0], "data_type": row[1]} for row in columns]

            cursor.close()
            connection.close()

            return {"status": "success", "schema": schema_info}
        except Exception as e:
            return {"status": "error", "message": str(e)}
