from pydantic import BaseModel, Field, field_validator
import pyodbc
import re
from src.ConvertToDQDataType import DQDataType

class SnowflakeBaseModel(BaseModel):
    user: str = Field(..., description="UserName must be provided")
    password: str = Field(..., description="Password must be provided")
    account: str = Field(..., description="Account must be provided")
    warehouse: str = Field(..., description="Warehouse must be provided")
    database: str = Field(..., description="Database must be provided")
    snowflakeschema: str = Field(..., description="Schema must be provided")

    @field_validator("account", mode="before")
    def validate_account(cls, value: str) -> str:        
        """
        Validate Snowflake account URL format.
        Accepts only valid FQDNs like '<account>.<region>.snowflakecomputing.com'.
        """
        if ';' in value or '=' in value or ' ' in value or '/' in value:
            raise ValueError("Account not authentic.")

       # Length restriction for total FQDN (DNS max is 253 chars)
        if len(value) > 253:
            raise ValueError("Account FQDN is too long (must be <= 253 characters).")

        # Subdomain constraints
        label = r"[a-z][a-z0-9-]{0,61}[a-z0-9]"  # standard DNS label, max 63 chars
        gov_prefix = r"(gov\.)?"                 # optional `gov.` in domain
        domain = rf"{label}\.{label}\.{gov_prefix}snowflakecomputing\.com"

        if not re.fullmatch(rf"^{domain}$", value, flags=re.IGNORECASE):
            raise ValueError(
                "Invalid Snowflake account format. Expected format: '<account>.<region>.snowflakecomputing.com'"
            )

        return value

    @field_validator("user", "password", "warehouse", "database", "snowflakeschema", mode="before")
    def validate_non_empty_fields(cls, value):
        """Ensure required fields are not empty."""
        if not value or not str(value).strip():
            raise ValueError("Field cannot be empty")
        return value

    def quote_identifier(self, identifier: str) -> str:
        """Ensure that the identifier is properly quoted for Snowflake."""
        return f'"{identifier}"' if not identifier.isupper() else identifier

    def get_connection_string(self):
        """Construct Snowflake ODBC connection string."""
        return (
            f"Driver=/usr/lib64/snowflake/odbc/lib/libSnowflake.so;"
            f"Server={self.account};"
            f"Database={self.quote_identifier(self.database)};"
            f"Schema={self.quote_identifier(self.snowflakeschema)};"
            f"UID={self.user};"
            f"PWD={self.password};"
            f"Warehouse={self.warehouse};"
            f"Port=443;"
            f"SSL=on;"
            f"AuthenticatingViaOAuth=false;"
        )

class SnowflakeDWRequest(SnowflakeBaseModel):
    """Handles Snowflake connection testing."""

    def test_connection(self):
        """Test Snowflake ODBC connection."""
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
    """Handles Snowflake table schema retrieval."""
    table: str = Field(..., description="Table Name must be provided")

    @field_validator("table", mode="before")
    def validate_table(cls, value):
        """Ensure table name is not empty."""
        if not value or not str(value).strip():
            raise ValueError("Table Name cannot be empty")
        return value

    def get_table_schema(self):
        """Fetch table schema from Snowflake."""
        try:
            conn = pyodbc.connect(self.get_connection_string(), autocommit=True)
            cursor = conn.cursor()
            quoted_table = self.quote_identifier(self.table)
            query = f"DESCRIBE TABLE {quoted_table}"
            
            cursor.execute(query)
            columns = cursor.fetchall()
            schema_info = [{"column_name": row[0], "dtype": row[1]} for row in columns]
            
            cursor.close()
            conn.close()

            schema = DQDataType().fnconvertToDQDataType(schema_list=schema_info, sourceType="snowflake")
            return schema

        except Exception as e:
            return {"status": "error", "message": str(e)}
