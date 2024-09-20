from pydantic import BaseModel
import pyodbc

class DatabricksUnityCatalogRequest(BaseModel):
    hostname: str
    http_path: str
    access_token: str

    def test_connection(hostname, http_path, access_token):
        port = 443  # Default port for Databricks ODBC

        # Create a connection string
        connection_string = (
            f"DRIVER={{Simba Spark ODBC Driver}};"
            f"HOST={hostname};"
            f"PORT={port};"
            f"HTTPPath={http_path};"
            f"AuthMech=3;"  # AuthMech=3 indicates token-based authentication
            f"UID=token;"
            f"PWD={access_token};"
            f"SparkServerType=3;"  # Use 3 for Databricks clusters
            f"SSL=1;"  # Enable SSL
            f"ThriftTransport=2;"  # Use HTTP transport mode
            f"SparkSQLCatalogImplementation=hive;"
        )

        try:
            # Establish a connection
            connection = pyodbc.connect(connection_string, autocommit=True)

            # Create a cursor and execute a test query
            cursor = connection.cursor()
            cursor.execute("SHOW CATALOGS")

            # Fetch results
            catalogs = cursor.fetchall()
            catalog_names = [catalog[0] for catalog in catalogs]

            # Close the cursor and connection
            cursor.close()
            connection.close()

            return {"status": "success", "catalogs": catalog_names}

        except Exception as e:
            return {"status": "error", "message": str(e)}

class DatabricksUnityCatalogSchemaRequest(BaseModel):
    hostname: str
    http_path: str
    access_token: str
    catalog: str
    unitycatalogschema: str
    table: str

    def get_table_schema(hostname, http_path, access_token, catalog, unitycatalogschema, table):
        port = 443  # Default port for Databricks ODBC

        # Create a connection string
        connection_string = (
            f"DRIVER={{Simba Spark ODBC Driver}};"
            f"HOST={hostname};"
            f"PORT={port};"
            f"HTTPPath={http_path};"
            f"AuthMech=3;"
            f"UID=token;"
            f"PWD={access_token};"
            f"SparkServerType=3;"
            f"SSL=1;"
            f"ThriftTransport=2;"
            f"SparkSQLCatalogImplementation=hive;"
        )

        try:
            # Establish a connection
            connection = pyodbc.connect(connection_string, autocommit=True)

            # Create a cursor and execute the query to get the table schema
            cursor = connection.cursor()
            query = f"DESCRIBE {catalog}.{unitycatalogschema}.{table}"
            cursor.execute(query)

            # Fetch the schema (column name and data type)
            columns = cursor.fetchall()
            schema_info = [{"column_name": row[0], "data_type": row[1]} for row in columns]

            # Close the cursor and connection
            cursor.close()
            connection.close()

            return {"status": "success", "schema": schema_info}

        except Exception as e:
            return {"status": "error", "message": str(e)}
