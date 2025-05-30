from typing import Dict, List, Any
import re

class DQDataType:

    def __init__(self):

        self.DATA_TYPE_MAPPINGS = {
            "iceberg": {
                "String": ["VARCHAR","UUID","TIME","JSON","INTERVAL","BIT","BLOB"],
                "Boolean": ["BOOLEAN"],
                "Number_integral": ["SMALLINT", "INTEGER","HUGEINT", "BIGINT", "TINYINT", "UBIGINT", "UHUGEINT", "UINTEGER", "USMALLINT", "UTINYINT"],
                "Number_non_integral": ["FLOAT", "DOUBLE"],
                "Decimal": ["DECIMAL", "NUMERIC"],
                "Date": ["DATE"],
                "DateTime": ["TIMESTAMP", "TIMESTAMPTZ"]
            },
            "azuresql": {
                "String": ["NVARCHAR", "VARCHAR", "VARBINARY", "CHAR", "TEXT","TIME", "UNIQUEIDENTIFIER"],
                "Boolean": ["BIT"],
                "Number_integral": ["SMALLINT", "INT", "BIGINT", "TINYINT"],
                "Number_non_integral": ["FLOAT", "REAL"],
                "Decimal": ["DECIMAL","NUMERIC"],
                "Date": ["DATE"],
                "DateTime": ["DATETIME", "DATETIME2", "SMALLDATETIME", "DATETIMEOFFSET", "TIMESTAMP"]
            },
            "snowflake": {
                "String": ["STRING", "VARCHAR", "TEXT", "CHAR", "CHARACTER", "NCHAR", "BINARY", "VARBINARY", "TIME", "MAP", "ARRAY", "UUID","JSON","INTERVAL","BIT","BLOB","VARIANT"],
                "Boolean": ["BOOLEAN"],
                "Number_integral": ["INT" , "INTEGER" , "BIGINT" , "SMALLINT" , "TINYINT" , "BYTEINT", "BIGINT"],
                "Number_non_integral": ["FLOAT" , "FLOAT4" , "FLOAT8", "DOUBLE", "REAL"],
                "Decimal": ["DECIMAL", "NUMERIC", "NUMBER"],
                "Date": ["DATE"],
                "DateTime": ["DATETIME", "TIMESTAMP" , "TIMESTAMP_NTZ", "TIMESTAMP_TZ", "TIMESTAMP_LTZ","TIMESTAMPTZ"]
            },
            "parquet": {
                "String": ["STRING", "LARGE_STRING", "UTF8","INTERVAL","BINARY","ARRAY","MAP","LIST"],
                "Boolean": ["BOOL","BOOLEAN"],
                "Number_integral": ["INT","LONG","INT8", "INT16", "INT32", "INT64", "UINT8", "UINT16", "UINT32", "UINT64"],
                "Number_non_integral": ["FLOAT16", "FLOAT32", "FLOAT64", "HALFFLOAT", "FLOAT","DOUBLE"],
                "Decimal": ["DECIMAL","DECIMAL128", "DECIMAL256"],
                "Date": ["DATE","DATE32", "DATE64"],
                "DateTime": ["TIMESTAMP","TIMESTAMP[NS]", "TIMESTAMP[US]", "TIMESTAMP[MS]", "TIMESTAMP[S]","TIMESTAMP[NS, TZ=UTC]", "TIMESTAMP[US, TZ=UTC]", "TIMESTAMP[MS, TZ=UTC]","TIMESTAMP[S, TZ=UTC]"]
                },
            "delta": {
                "String": ["STRING", "VARCHAR", "CHAR","INTERVAL", "BINARY","ARRAY","MAP","VARIANT"],
                "Boolean": ["BOOLEAN"],
                "Number_integral": ["BYTE", "SHORT", "INT", "BIGINT", "LONG","INTEGER","TINYINT", "SMALLINT"],
                "Number_non_integral": ["FLOAT", "DOUBLE"],
                "Decimal": ["DECIMAL"],
                "Date": ["DATE"],
                "DateTime": ["TIMESTAMP","TIMESTAMP_NTZ"]
                },
            "bigquery": {
                "String": ["STRING", "ARRAY", "BYTES", "GEOGRAPHY", "INTERVAL", "JSON", "STRUCT", "TIME"],
                "Boolean": ["BOOL", "BOOLEAN"],
                "Number_integral": ["INT64", "INTEGER", "INT", "SMALLINT", "BIGINT", "TINYINT", "BYTEINT"],
                "Number_non_integral": ["FLOAT64", "FLOAT"],
                "Decimal": ["NUMERIC", "BIGNUMERIC"],
                "Date": ["DATE"],
                "DateTime": ["DATETIME","TIMESTAMP"]
                },
            "synapsededicateddw": {
                "String": ["NVARCHAR", "VARCHAR", "VARBINARY", "CHAR", "TEXT","TIME", "UNIQUEIDENTIFIER"],
                "Boolean": ["BIT"],
                "Number_integral": ["SMALLINT", "INT", "BIGINT", "TINYINT"],
                "Number_non_integral": ["FLOAT", "REAL"],
                "Decimal": ["DECIMAL", "NUMERIC"],
                "Date": ["DATE"],
                "DateTime": ["DATETIME", "DATETIME2", "SMALLDATETIME", "DATETIMEOFFSET", "TIMESTAMP"]
            },
            "synapseserverless": {
                "String": ["NVARCHAR", "VARBINARY", "VARCHAR", "CHAR", "STRING", "TIME", "UNIQUEIDENTIFIER"],
                "Boolean": ["BIT"],
                "Number_integral": ["TINYINT", "SMALLINT", "INT", "BIGINT"],
                "Number_non_integral": ["FLOAT", "REAL"],
                "Decimal": ["DECIMAL", "NUMERIC"],
                "Date": ["DATE"],
                "DateTime": ["DATETIME", "DATETIME2", "SMALLDATETIME", "DATETIMEOFFSET", "TIMESTAMP"]
            }
        }

    # Convert schema based on sourceType
    def fnconvertToDQDataType(self, schema_list: List[Dict[str, str]], sourceType: str = "iceberg") -> Dict[str, Any]:
        dq_schema = []
        type_mapping = self.DATA_TYPE_MAPPINGS.get(sourceType.lower())

        if not type_mapping:
            raise ValueError(f"Unsupported source type: {sourceType}")

        for column in schema_list:
            column_name = column.get("column_name")
            dtype = column.get("dtype", "").upper()

            if not column_name or not dtype:
                raise ValueError(f"Invalid schema column definition: {column}")

            # Extract the base type using regex
            dtype_match = re.match(r"^([A-Z]+)", dtype)
            if dtype_match:
                dtype = dtype_match.group(1)
            else:
                raise ValueError(f"Invalid data type '{dtype}' for column '{column_name}'.")

            dq_column = {"name": column_name}

            # Map types based on source-specific mappings
            for key, value in type_mapping.items():
                if dtype in value:
                    dq_column["type"] = key
                    if key == "Number_integral":
                        dq_column["type"] = "Number"
                        dq_column["typeProperties"] = {"integral": True}
                    elif key == "Number_non_integral":
                        dq_column["type"] = "Number"
                        dq_column["typeProperties"] = {"integral": False}
                    elif key == "Decimal":
                        dq_column["type"] = "Number"
                        dq_column["typeProperties"] = {
                            "integral": False,
                            "precision": 38,
                            "scale": 18
                        }
                    elif key == "Date":
                        dq_column["typeProperties"] = {"formats": ["YYYY-MM-DD"]}
                    break
            else:
                raise ValueError(f"Unsupported data type '{dtype}' for column '{column_name}' in source '{sourceType}'.")

            dq_schema.append(dq_column)

        return {"status": "success", "schema": dq_schema}