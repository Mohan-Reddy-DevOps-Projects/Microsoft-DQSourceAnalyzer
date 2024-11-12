from typing import Dict, List, Any

class DQDataType:

    def __init__(self):

        self.DATA_TYPE_MAPPINGS = {
            "iceberg": {
                "String": ["VARCHAR","UUID","TIME","JSON","INTERVAL","BIT"],
                "Boolean": ["BOOLEAN"],
                "Number_integral": ["SMALLINT", "INTEGER","HUGEINT", "BIGINT", "TINYINT", "UBIGINT", "UHUGEINT", "UINTEGER", "USMALLINT", "UTINYINT"],
                "Number_non_integral": ["FLOAT", "DOUBLE"],
                "Decimal": ["DECIMAL","DECIMAL(18,3)", "NUMERIC"],
                "Date": ["DATE"],
                "DateTime": ["TIMESTAMP", "TIMESTAMPTZ"]
            },
            "azuresql": {
                # Define Azure SQL mappings
                "String": ["NVARCHAR", "VARCHAR", "CHAR", "TEXT"],
                "Boolean": ["BIT"],
                "Number_integral": ["SMALLINT", "INT", "BIGINT", "TINYINT"],
                "Number_non_integral": ["FLOAT", "REAL", "NUMERIC"],
                "Decimal": ["DECIMAL"],
                "Date": ["DATE"],
                "DateTime": ["DATETIME", "DATETIME2", "TIMESTAMP"]
            },
            "snowflake": {
                # Define Snowflake mappings
                "String": ["STRING", "VARCHAR", "TEXT"],
                "Boolean": ["BOOLEAN"],
                "Number_integral": ["INT", "BIGINT", "SMALLINT"],
                "Number_non_integral": ["FLOAT", "DOUBLE", "NUMBER"],
                "Decimal": ["NUMBER"],
                "Date": ["DATE"],
                "DateTime": ["TIMESTAMP_NTZ", "TIMESTAMP_TZ", "TIMESTAMP_LTZ"]
            }
            # Add other sources like Databricks Unity Catalog here as needed
        }

    # Convert schema based on sourceType
    def fnconvertToDQDataType(self, schema_list: List[Dict[str, str]], sourceType: str = "iceberg") -> Dict[str, Any]:
        dq_schema = []
        type_mapping = self.DATA_TYPE_MAPPINGS.get(sourceType.lower())

        if not type_mapping:
            raise ValueError(f"Unsupported source type: {sourceType}")

        for column in schema_list:
            column_name = column["column_name"]
            dtype = column["dtype"]
            dq_column = {"name": column_name}

            # Map types based on source-specific mappings
            if dtype in type_mapping["String"]:
                dq_column["type"] = "String"
            
            elif dtype in type_mapping["Boolean"]:
                dq_column["type"] = "Boolean"
            
            elif dtype in type_mapping["Number_integral"]:
                dq_column["type"] = "Number"
                dq_column["typeProperties"] = {"integral": True}
            
            elif dtype in type_mapping["Number_non_integral"]:
                dq_column["type"] = "Number"
                dq_column["typeProperties"] = {"integral": False}
            
            elif dtype in type_mapping["Decimal"]:
                dq_column["type"] = "Number"
                dq_column["typeProperties"] = {
                    "integral": False,
                    "precision": 38,  # Default precision value
                    "scale": 38       # Default scale value
                }
            
            elif dtype in type_mapping["Date"]:
                dq_column["type"] = "Date"
                dq_column["typeProperties"] = {
                    "formats": ["YYYY-MM-DD"]
                }
            
            elif dtype in type_mapping["DateTime"]:
                dq_column["type"] = "DateTime"
            
            else:
                # Raise exception for unsupported types
                raise ValueError(f"Unsupported data type '{dtype}' for column '{column_name}' in source '{sourceType}'.")

            dq_schema.append(dq_column)

        return {"status": "success", "schema": dq_schema}