from pydantic import BaseModel
from databricks import sql

class DatabricksUnityCatalogRequest(BaseModel):
    hostname: str
    http_path: str
    access_token: str

    def test_connection(hostname, http_path, access_token):
        try:
            conn = sql.connect(
                server_hostname=hostname,
                http_path=http_path,
                access_token=access_token,
            )
            cursor = conn.cursor()
            cursor.execute(f"SHOW CATALOGS")

            catalogs = cursor.fetchall()
            catalog_names = [catalog[0] for catalog in catalogs]

            cursor.close()
            conn.close()

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
        try:
            conn = sql.connect(
                server_hostname=hostname,
                http_path=http_path,
                access_token=access_token,
            )

            cursor = conn.cursor()
            query = f"DESCRIBE TABLE {catalog}.{unitycatalogschema}.{table}"
            cursor.execute(query)

            # Fetch the schema (column name and data type)
            columns = cursor.fetchall()
            schema_info = [{"column_name": row[0], "data_type": row[1]} for row in columns]

            cursor.close()
            conn.close()

            return {"status": "success", "schema": schema_info}

        except Exception as e:
            return {"status": "error", "message": str(e)}
