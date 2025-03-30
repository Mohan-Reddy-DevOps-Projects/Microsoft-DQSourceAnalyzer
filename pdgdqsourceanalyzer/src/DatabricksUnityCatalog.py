from pydantic import BaseModel, Field, field_validator
import pyodbc
from src.ConvertToDQDataType import DQDataType
import re

class DatabricksBaseModel(BaseModel):
    hostname: str = Field(..., description="Databricks hostname must be provided")
    http_path: str = Field(..., description="Databricks HTTP path must be provided")
    access_token: str = Field(..., description="Access token must be provided")
    catalog: str = Field(..., description="Databricks catalog must be provided")
    unitycatalogschema: str = Field(..., description="Databricks schema must be provided")

    @field_validator('hostname')
    def validate_hostname(cls, value):
        """Validate Databricks hostname format."""
        pattern = r"^https:\/\/adb-\d+\.\d+\.azuredatabricks\.net$"
        if not re.match(pattern, value):
            raise ValueError("Invalid Databricks hostname. Must follow 'https://adb-<unique-id>.<shard>.azuredatabricks.net' format.")
        return value    

    @field_validator('hostname', 'http_path', 'access_token', 'catalog', 'unitycatalogschema')
    def field_not_empty(cls, value):
        if not value:
            raise ValueError('Field cannot be empty')
        return value

    def get_connection_string(self):
        port = 443  # Default port for Databricks ODBC
        return (
            f"Driver=/opt/simba/spark/lib/64/libsparkodbc_sb64.so;"
            f"HOST={self.hostname};"
            f"PORT={port};"
            f"HTTPPath={self.http_path};"
            f"AuthMech=3;"  # Token-based authentication
            f"UID=token;"
            f"PWD={self.access_token};"
            f"SparkServerType=3;"  # Databricks clusters
            f"SSL=1;"  # Enable SSL
            f"ThriftTransport=2;"  # HTTP transport mode
            f"SparkSQLCatalogImplementation=hive;"
        )

class DatabricksUnityCatalogRequest(DatabricksBaseModel):
    def test_connection(self):
        try:
            connection = pyodbc.connect(self.get_connection_string(), autocommit=True)
            cursor = connection.cursor()

            cursor.execute(f"USE {self.catalog}.{self.unitycatalogschema};")
            cursor.execute("SELECT CURRENT_CATALOG(), CURRENT_METASTORE();")
            result = cursor.fetchone()
            current_catalog, current_metastore = result[0], result[1]
            current_metastore = current_metastore.split(":")[-1]

            cursor.close()
            connection.close()
            return {"status": "success","current_catalog": current_catalog,"current_metastore": current_metastore}

        except Exception as e:
            return {"status": "error", "message": str(e)}

class DatabricksUnityCatalogSchemaRequest(DatabricksBaseModel):
    table: str = Field(..., description="Table name must be provided")

    @field_validator('table')
    def field_not_empty(cls, value):
        if not value:
            raise ValueError('Field cannot be empty')
        return value

    def get_table_schema(self):
        try:
            connection = pyodbc.connect(self.get_connection_string(), autocommit=True)
            cursor = connection.cursor()
            query = f"DESCRIBE {self.catalog}.{self.unitycatalogschema}.{self.table}"
            cursor.execute(query)

            columns = cursor.fetchall()
            schema_info = [{"column_name": row[0], "dtype": row[1]} for row in columns]

            cursor.close()
            connection.close()
            
            schema = DQDataType().fnconvertToDQDataType(schema_list=schema_info,sourceType="delta")

            return schema

        except Exception as e:
            return {"status": "error", "message": str(e)}
