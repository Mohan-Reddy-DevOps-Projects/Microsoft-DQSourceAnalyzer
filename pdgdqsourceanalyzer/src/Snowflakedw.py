from pydantic import BaseModel, Field, field_validator
import pyodbc

class SnowflakeBaseModel(BaseModel):
    user: str = Field(..., description="UserName must be provided")
    password: str = Field(..., description="Password must be provided")
    account: str = Field(..., description="Account must be provided")
    warehouse: str = Field(..., description="Warehouse must be provided")
    database: str = Field(..., description="Database must be provided")
    snowflakeschema: str = Field(..., description="Schema must be provided")

    @field_validator('user', 'password', 'account', 'warehouse', 'database', 'snowflakeschema')
    def field_not_empty(cls, value):
        if not value:
            raise ValueError('Field cannot be empty')
        return value

    def get_connection_string(self):
        return (
            f"Driver=/usr/lib64/snowflake/odbc/lib/libSnowflake.so;"  # Snowflake ODBC driver path
            f"Server={self.account};"  # Snowflake server hostname
            f"Database={self.database};"  # Snowflake database
            f"Schema={self.snowflakeschema};"  # Snowflake schema
            f"UID={self.user};"  # Snowflake user ID
            f"PWD={self.password};"  # Snowflake password
            f"Warehouse={self.warehouse};"  # Snowflake warehouse
            f"Port=443;"  # Snowflake uses port 443 by default for ODBC
            f"SSL=on;"  # Enable SSL for secure connection
            f"AuthenticatingViaOAuth=false;"  # If not using OAuth (optional)
        )

class SnowflakeDWRequest(SnowflakeBaseModel):
    def test_connection(self):
        try:
            conn = pyodbc.connect(self.get_connection_string(), autocommit=True)
            cursor = conn.cursor()
            cursor.execute("SHOW SCHEMAS")
            schemas = cursor.fetchall()
            schema_names = [schema[1] for schema in schemas]
            cursor.close()
            conn.close()

            return {"status": "success", "schemas": schema_names}

        except Exception as e:
            return {"status": "error", "message": str(e)}

class SnowflakeDWSchemaRequest(SnowflakeBaseModel):
    table: str = Field(..., description="Table Name must be provided")

    @field_validator('table')
    def field_not_empty(cls, value):
        if not value:
            raise ValueError('Field cannot be empty')
        return value

    def get_table_schema(self):
        try:
            conn = pyodbc.connect(self.get_connection_string(), autocommit=True)
            cursor = conn.cursor()
            query = f"DESCRIBE TABLE {self.table}"
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
