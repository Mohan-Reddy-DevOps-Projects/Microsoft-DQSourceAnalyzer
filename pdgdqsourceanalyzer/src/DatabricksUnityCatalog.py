from pydantic import BaseModel, Field, field_validator
import pyodbc
from src.ConvertToDQDataType import DQDataType
import re
from src.validators import SourceValidators

class DatabricksBaseModel(BaseModel):
    hostname: str = Field(..., description="Databricks hostname must be provided")
    http_path: str = Field(..., description="Databricks HTTP path must be provided")
    access_token: str = Field(..., description="Access token must be provided")
    catalog: str = Field(..., description="Databricks catalog must be provided")
    unitycatalogschema: str = Field(..., description="Databricks schema must be provided")

    @field_validator("hostname", mode="before")
    def validate_url(cls, value):
        return SourceValidators.validate_hostname(value)
    
    @field_validator("http_path", mode="before")
    def validate_http_path(cls, value):
        return SourceValidators.validate_databricks_http_path(value)

    @field_validator("catalog","unitycatalogschema", mode="before")
    def validate_identifier(cls, value):
        return SourceValidators.validate_unity_catalog(value)    
    
    @field_validator('http_path', 'access_token', 'catalog', 'unitycatalogschema', 'hostname')
    def check_not_empty(cls, value):
        return SourceValidators.not_empty(value)

    def get_connection_string(self):
        """Generate Databricks ODBC connection string."""
        port = 443  # Default Databricks ODBC port
        return (
            f"Driver=/opt/simba/spark/lib/64/libsparkodbc_sb64.so;"
            f"HOST={self.hostname};"
            f"PORT={port};"
            f"HTTPPath={self.http_path};"
            f"AuthMech=3;"  # Token-based authentication
            f"UID=token;"
            f"PWD={self.access_token};"
            f"SparkServerType=3;"  # Databricks cluster type
            f"SSL=1;"  # Enable SSL
            f"ThriftTransport=2;"  # HTTP transport mode
            f"SparkSQLCatalogImplementation=hive;"
        )

class DatabricksUnityCatalogRequest(DatabricksBaseModel):
    def test_connection(self):
        """Test Databricks connection."""
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
            return {"status": "success", "current_catalog": current_catalog, "current_metastore": current_metastore}

        except Exception as e:
            return {"status": "error", "message": str(e)}

class DatabricksUnityCatalogSchemaRequest(DatabricksBaseModel):
    table: str = Field(..., description="Table name must be provided")

    @field_validator("catalog","table", mode="before")
    def validate_url(cls, value):
        return SourceValidators.validate_unity_catalog(value) 

    @field_validator('table')
    def check_not_empty(cls, value):
        return SourceValidators.not_empty(value)
        
    def get_table_schema(self):
        """Retrieve schema for a table in Databricks Unity Catalog."""
        try:
            connection = pyodbc.connect(self.get_connection_string(), autocommit=True)
            cursor = connection.cursor()
            query = f"DESCRIBE {self.catalog}.{self.unitycatalogschema}.{self.table}"
            cursor.execute(query)

            columns = cursor.fetchall()

            # Robustly parse rows, skipping headers, partition metadata, and empty rows
            schema_info = []
            for row in columns:
                col_name = row[0]
                dtype = row[1] if len(row) > 1 else None

                if (
                    col_name is None or
                    col_name.strip() == "" or
                    col_name.strip().startswith("#") or
                    dtype is None
                ):
                    continue

                schema_info.append({
                    "column_name": col_name.strip(),
                    "dtype": dtype.strip()
                })

            cursor.close()
            connection.close()
            schema = DQDataType().fnconvertToDQDataType(schema_list=schema_info, sourceType="delta")
            return schema
        except Exception as e:
            return {"status": "error", "message": str(e)}

