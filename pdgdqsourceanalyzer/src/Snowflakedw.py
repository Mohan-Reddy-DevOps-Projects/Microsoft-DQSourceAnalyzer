from pydantic import BaseModel
import snowflake.connector

class SnowflakeDWRequest(BaseModel):
    user: str
    password: str
    account: str
    warehouse: str
    database: str
    snowflakeschema: str

    def test_connection(account, user, password, warehouse, database, snowflakeschema):
        try:
            # Establish a connection
            conn = snowflake.connector.connect(
                user=user,
                password=password,
                account=account,
                warehouse=warehouse,
                database=database,
                schema=snowflakeschema
            )

            # Create a cursor and execute a test query
            cursor = conn.cursor()
            cursor.execute("SHOW SCHEMAS")

            # Fetch results
            schemas = cursor.fetchall()
            schema_names = [schema[1] for schema in schemas]  # Adjust index as needed

            # Close the cursor and connection
            cursor.close()
            conn.close()

            return {"status": "success", "schemas": schema_names}

        except Exception as e:
            return {"status": "error", "message": str(e)}

class SnowflakeDWSchemaRequest(BaseModel):
    user: str
    password: str
    account: str
    warehouse: str
    database: str
    snowflakeschema: str
    table: str

    def get_table_schema(account, user, password, warehouse, database, snowflakeschema, table):
        try:
            # Establish a connection
            conn = snowflake.connector.connect(
                user=user,
                password=password,
                account=account,
                warehouse=warehouse,
                database=database,
                schema=snowflakeschema
            )

            # Create a cursor and execute the query to get the table schema
            cursor = conn.cursor()
            query = f"DESCRIBE TABLE {table}"
            cursor.execute(query)

            # Fetch the schema (column name and data type)
            columns = cursor.fetchall()
            schema_info = [{"column_name": row[0], "data_type": row[1]} for row in columns]

            # Close the cursor and connection
            cursor.close()
            conn.close()

            return {"status": "success", "schema": schema_info}

        except Exception as e:
            return {"status": "error", "message": str(e)}