from pydantic import BaseModel, Field, field_validator
import snowflake.connector

class SnowflakeDWRequest(BaseModel):
    user: str = Field(..., description="UserName must be provided")
    password: str = Field(..., description="Password must be provided")
    account: str = Field(..., description="Account must be provided")
    warehouse: str = Field(..., description="Warehouse must be provided")
    database: str = Field(..., description="Database must be provided")
    snowflakeschema: str = Field(..., description="Schema must be provided")
    
    @field_validator('user','password','account','warehouse','database','snowflakeschema')
    def field_not_empty(cls, value):
        if not value:
            raise ValueError('Field cannot be empty')
        return value

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
    user: str = Field(..., description="UserName must be provided")
    password: str = Field(..., description="Password must be provided")
    account: str = Field(..., description="Account must be provided")
    warehouse: str = Field(..., description="Warehouse must be provided")
    database: str = Field(..., description="Database must be provided")
    snowflakeschema: str = Field(..., description="Schema must be provided")
    table: str = Field(..., description="Table Name must be provided")
    
    @field_validator('user','password','account','warehouse','database','snowflakeschema','table')
    def field_not_empty(cls, value):
        if not value:
            raise ValueError('Field cannot be empty')
        return value

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