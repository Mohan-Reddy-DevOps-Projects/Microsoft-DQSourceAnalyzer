from pydantic import BaseModel, Field, field_validator
import pyodbc
from azure.identity import DefaultAzureCredential
from typing import List, Dict
from src.CustomTokenCredentialHelper import CustomTokenCredential
import struct
import re
from src.ConvertToDQDataType import DQDataType
from src.validators import SourceValidators

class AzureSQLBaseModel(BaseModel):
    server: str = Field(..., description="Server must be provided")
    database: str = Field(..., description="Database must be provided")
    token: str = Field(..., description="Token must be provided")
    expires_on: int = Field(..., description="Token Expiration must be provided")

    @field_validator("server", mode="before")
    def validate_url(cls, value):
        return SourceValidators.validate_server(value)

    @field_validator('database', 'token', 'expires_on')
    def check_not_empty(cls, value):
        return SourceValidators.not_empty(value)

    def get_token_struct(self) -> bytes:
        """Generate token struct for ODBC authentication."""
        credential = CustomTokenCredential(token=self.token, expires_on=self.expires_on)
        token = credential.get_token().token
        exptoken = b''.join([bytes({i}) + bytes(1) for i in bytes(token, "UTF-8")])
        return struct.pack("=i", len(exptoken)) + exptoken

    def connect_to_azure_sql(self, query: str = None) -> Dict[str, str]:
        """Create a connection to Azure SQL and optionally execute a query."""
        try:
            tokenstruct = self.get_token_struct()
            connection_string = (
                f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                f"SERVER={self.server};"
                f"DATABASE={self.database};"
                f"TrustServerCertificate=yes;"
            )
            connection = pyodbc.connect(connection_string, attrs_before={1256: tokenstruct})
            cursor = connection.cursor()

            if query:
                cursor.execute(query)
                result = cursor.fetchall()
            else:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()

            cursor.close()
            connection.close()
            return {"status": "success", "result": result if query else "Connection successful"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

class AzureSQLRequest(AzureSQLBaseModel):
    def test_connection(self) -> Dict[str, str]:
        """Test connection to Azure SQL."""
        return self.connect_to_azure_sql()

class AzureSQLSchemaRequest(AzureSQLBaseModel):
    table: str = Field(..., description="Table Name must be provided")
    schema: str = Field(..., description="Schema Name must be provided")

    @field_validator('table','schema')
    def check_not_empty(cls, value):
        return SourceValidators.not_empty(value)

    def get_table_schema(self) -> Dict[str, List[Dict[str, str]]]:
        """Retrieve table schema from Azure SQL."""
        query = f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{self.table}' AND TABLE_SCHEMA ='{self.schema}'"
        result = self.connect_to_azure_sql(query)

        if result["status"] == "success":
            columns = result["result"]
            schema_info = [{"column_name": row[0], "dtype": row[1]} for row in columns]
            schema = DQDataType().fnconvertToDQDataType(schema_list=schema_info, sourceType="azuresql")
            return schema
        else:
            return result
