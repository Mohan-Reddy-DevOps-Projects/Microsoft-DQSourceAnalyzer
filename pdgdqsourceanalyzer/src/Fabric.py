from pydantic import BaseModel, Field, field_validator
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.storage.filedatalake import DataLakeServiceClient
from typing import List, Dict
from deltalake import DeltaTable
import pyarrow.parquet as pq
from azure.storage.filedatalake import DataLakeServiceClient
import pyarrow.dataset as ds
import duckdb
import json,os
from fsspec import filesystem
from adlfs import AzureBlobFileSystem
from src.CustomTokenCredentialHelper import CustomTokenCredential
from src.ConvertToDQDataType import DQDataType

class FabricRequest(BaseModel):
    account_name: str = Field(..., description="Storage account name must be provided")
    file_system_name: str = Field(..., description="File System Name must be provided")
    directory_path: str = Field(..., description="Directory Path must be provided")
    token: str = Field(..., description="Token must be provided")
    expires_on: int = Field(..., description="Token Expiration must be provided")

    @field_validator("account_name", mode="before")
    def validate_account_name(cls, value: str) -> str:
        """
        Only 'onelake' (all lowercase) is accepted as a valid account_name.
        """
        value = value.strip()
        if value != "onelake":
            raise ValueError("Invalid account_name. Only lowercase 'onelake' is allowed.")
        return value
    
    @field_validator('account_name', 'file_system_name', 'directory_path','token','expires_on')
    def field_not_empty(cls, value):
        if not value:
            raise ValueError('Field cannot be empty')
        return value

    def test_connection(account_name: str, file_system_name: str, directory_path: str, token:str,expires_on:int) -> Dict[str, str]:
        try:
            credential = CustomTokenCredential(token=token,expires_on=expires_on)
            account_url = f"https://{account_name}.dfs.fabric.microsoft.com"                
            service_client = DataLakeServiceClient(account_url=account_url, credential=credential)

            # Check if the directory exists
            file_system_client = service_client.get_file_system_client(file_system=file_system_name)
            directory_client = file_system_client.get_directory_client(directory_path)
            if not directory_client.exists():
                return {"status": "error", "message": "Directory does not exist"}
            return {"status": "success", "result": "Connection successful"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

class FabricDeltaSchemaRequest(BaseModel):
    account_name: str = Field(..., description="Storage account name must be provided") #storageaccountname
    file_system_name: str = Field(..., description="File System Name must be provided") #mycontainer
    directory_path: str = Field(..., description="Directory Path must be provided")  #"someDeltapath/mytable"
    token: str = Field(..., description="Token must be provided")
    expires_on: int = Field(..., description="Token Expiration must be provided")    
    
    @field_validator('account_name', 'file_system_name', 'directory_path','token','expires_on')
    def field_not_empty(cls, value):
        if not value:
            raise ValueError('Field cannot be empty')
        return value

    def get_table_schema(account_name: str, file_system_name: str, directory_path: str,token:str,expires_on:int) -> Dict[str, List[Dict[str, str]]]:
        try:
            credential = CustomTokenCredential(token=token,expires_on=expires_on)
            storage_options={"bearer_token": token, "use_fabric_endpoint": "true"}
            arrow_table = DeltaTable(
                f"abfss://{file_system_name}@{account_name}.dfs.fabric.microsoft.com/{directory_path}",
                storage_options=storage_options
            ).schema().fields
            schema_list = [{"column_name": field.name, "dtype": str(field.type.type)} for field in arrow_table]
            # Fetch schema
            schema = DQDataType().fnconvertToDQDataType(schema_list=schema_list,sourceType="delta")
            return schema
        except Exception as e:
            return {"status": "error", "message": str(e)}

class FabricIcebergSchemaRequest(BaseModel):
    account_name: str = Field(..., description="Storage account name must be provided") #storageaccountname
    file_system_name: str = Field(..., description="File System Name must be provided") #mycontainer
    directory_path: str = Field(..., description="Directory Path must be provided")  #"someDeltapath/mytable"
    token: str = Field(..., description="Token must be provided")
    expires_on: int = Field(..., description="Token Expiration must be provided")    
    
    @field_validator('account_name', 'file_system_name', 'directory_path','token','expires_on')
    def field_not_empty(cls, value):
        if not value:
            raise ValueError('Field cannot be empty')
        return value

    def get_table_schema(account_name: str, file_system_name: str, directory_path: str,token:str,expires_on:int) -> Dict[str, List[Dict[str, str]]]:
        try:
            #credential = DefaultAzureCredential()
            credential = CustomTokenCredential(token=token,expires_on=expires_on)
            fs= AzureBlobFileSystem(account_name="onelake", anon=False, credential=credential)
            fs.account_host = "onelake.blob.fabric.microsoft.com"
            fs.do_connect()
            conn = duckdb.connect()
            try:
                conn.register_filesystem(fs)
                conn.sql("INSTALL iceberg; LOAD iceberg;")
                schema_result = conn.sql(
                    f"DESCRIBE (SELECT * FROM iceberg_scan('abfs://{file_system_name}@{account_name}.dfs.fabric.microsoft.com/{directory_path}', allow_moved_paths=true) LIMIT 1)"
                ).fetchall()
                schema_list = [{"column_name": schema[0], "dtype": "TIMESTAMP" if schema[1]=="TIMESTAMP WITH TIME ZONE" else schema[1]} for schema in schema_result]
                conn.unregister_filesystem(name="abfs")
                schemaResponse = DQDataType().fnconvertToDQDataType(schema_list=schema_list,sourceType="iceberg")
                return schemaResponse
            except Exception as e:
                return {"status": "error", "message": str(e)}
            finally:
                conn.close()
        except Exception as e:
            return {"status": "error", "message": str(e)}
        
class FabricParquetSchemaRequest(BaseModel):
    account_name: str = Field(..., description="Storage account name must be provided") #storageaccountname
    file_system_name: str = Field(..., description="File System Name must be provided") #mycontainer
    directory_path: str = Field(..., description="Directory Path must be provided")  #"someDeltapath/mytable"
    token: str = Field(..., description="Token must be provided")
    expires_on: int = Field(..., description="Token Expiration must be provided")    
    
    @field_validator('account_name', 'file_system_name', 'directory_path','token','expires_on')
    def field_not_empty(cls, value):
        if not value:
            raise ValueError('Field cannot be empty')
        return value
        
    def get_table_schema(account_name, file_system_name, directory_path,token:str,expires_on:int):
        #credential = DefaultAzureCredential()
        credential = CustomTokenCredential(token=token,expires_on=expires_on)
        try:
            fs= AzureBlobFileSystem(account_name="onelake", anon=False, credential=credential)
            fs.account_host = "onelake.blob.fabric.microsoft.com"
            fs.do_connect()
            full_path = f"{file_system_name}/{directory_path}"
            dataset = ds.dataset(full_path, filesystem=fs, format="parquet" , partitioning="hive")
            parquet_schema = dataset.schema

            schema_list = [{"column_name": field.name, "dtype": str(field.type)} for field in parquet_schema]
            if not schema_list:
                return {"status": "error", "message": "The specified directory is empty or does not exist."}
            else:
                schema = DQDataType().fnconvertToDQDataType(schema_list=schema_list,sourceType="parquet")
                return schema
        
        except Exception as e:
            return {"status": "error", "message": str(e)}
        

class FabricFormatDetector(BaseModel):
    account_name: str = Field(..., description="Storage account name must be provided") #storageaccountname
    file_system_name: str = Field(..., description="File System Name must be provided") #mycontainer
    directory_path: str = Field(..., description="Directory Path must be provided")  #"someDeltapath/mytable"
    token: str = Field(..., description="Token must be provided")
    expires_on: int = Field(..., description="Token Expiration must be provided")    
    
    @field_validator('account_name', 'file_system_name', 'directory_path','token','expires_on')
    def field_not_empty(cls, value):
        if not value:
            raise ValueError('Field cannot be empty')
        return value

    def detect_format(account_name, file_system_name, directory_path,token:str,expires_on:int) -> str:
        """
        Detect the format of the directory (Delta or Parquet) on ADLS Gen2.
        Returns:
            - "iceberg":If the directory is in Iceberg format.
            - "delta": If the directory is in Delta format.
            - "parquet": If the directory is in Parquet format.
            - "unsupportedFormat": If neither format is detected.
        """
        try:
            #credential = DefaultAzureCredential()
            credential = CustomTokenCredential(token=token,expires_on=expires_on)
            full_path = f"{file_system_name}/{directory_path}"
            # Try to detect Iceberg format
            try:
                fs= AzureBlobFileSystem(account_name="onelake", anon=False, credential=credential)
                fs.account_host = "onelake.blob.fabric.microsoft.com"
                fs.do_connect()
                conn = duckdb.connect()
                try:
                    conn.register_filesystem(fs)
                    conn.sql("INSTALL iceberg; LOAD iceberg;")
                    result = conn.sql(
                        f"DESCRIBE (SELECT * FROM iceberg_scan('abfs://{file_system_name}@{account_name}.dfs.fabric.microsoft.com/{directory_path}', allow_moved_paths=true) LIMIT 1)"
                    ).fetchall()
                    conn.unregister_filesystem(name="abfs")
                    return {"status": "success", "format": "iceberg" }
                except Exception as e:
                    pass
                finally:
                    conn.close()
            except Exception:
                # Not a Iceberg format, proceed to check for Delta Format
                pass
            # Try to detect Delta format
            try:
                storage_options={"bearer_token": token, "use_fabric_endpoint": "true"}
                #fs = AzureBlobFileSystem(account_name=account_name, credential=credential)
                delta_table = DeltaTable(f"abfss://{file_system_name}@{account_name}.dfs.fabric.microsoft.com/{directory_path}", storage_options=storage_options)
                # If no error, it's a Delta format
                return {"status": "success", "format": "delta" }
            except Exception:
                # Not a Delta format, proceed to check for Parquet
                pass
            # Try to detect Parquet format
            try:
                # Attempt to read the directory as a Parquet dataset
                dataset = ds.dataset(full_path, filesystem=fs, format="parquet" , partitioning="hive")
                parquet_schema = dataset.schema
                schema_list = [{"column_name": field.name, "dtype": str(field.type)} for field in parquet_schema]
                if not schema_list:
                    return {"status": "error", "message": "The specified directory is empty or does not exist."}
                else:    
                # If no error, it's a Parquet format
                    return {"status": "success", "format": "parquet" }
            except Exception:
                # Not a Parquet format either
                pass
            # If neither format is detected
            return {"status": "success", "format": "unsupportedFormat" }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def detect_partitions(account_name, file_system_name, directory_path,token:str,expires_on:int) -> str:
        """
        Detect if the (Parquet) directory on ADLS Gen2 is partitioned. Applies to only PARQUET
        Returns:
            - "isPartitioned": True - if partitioned else False
            - "partitionedColumns": Returns Partitioned Columns, else []
        """
        try:
            isPartitioned = False
            partition_columns = []
            #credential = DefaultAzureCredential()
            credential = CustomTokenCredential(token=token,expires_on=expires_on)
            full_path = f"{file_system_name}/{directory_path}"
            ##Get Partition Columns for Delta and Parquet formats.
            fs= AzureBlobFileSystem(account_name="onelake", anon=False, credential=credential)
            fs.account_host = "onelake.blob.fabric.microsoft.com"
            fs.do_connect()
            parquet_schema = ds.dataset(full_path, filesystem=fs, format="parquet", partitioning=None).schema
            partitioning = ds.dataset(full_path, filesystem=fs, format="parquet" , partitioning="hive").partitioning
            # Extract the partitioned columns (only if partitioning exists and is valid)
            if partitioning is not None and hasattr(partitioning, 'schema'):
                partition_columns = [{"column_name": col.name, "dtype": str(col.type)} for col in partitioning.schema if col.name not in parquet_schema.names]
                if partition_columns:
                    isPartitioned = True
            return {"status": "success", "isPartitioned": isPartitioned,"partition_columns":partition_columns}
        except Exception as e:
            return {"status": "error", "message": str(e)}
