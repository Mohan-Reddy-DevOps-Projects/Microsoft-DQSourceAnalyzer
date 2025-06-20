import re
from urllib.parse import urlparse
from pydantic import BaseModel, Field, field_validator
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.storage.filedatalake import DataLakeServiceClient
from typing import List, Dict
from deltalake import DeltaTable
import json,os
import pyarrow.parquet as pq
from azure.storage.filedatalake import DataLakeServiceClient
from azure.identity import DefaultAzureCredential
import pyarrowfs_adlgen2
import pyarrow
import pyarrow.dataset as ds
import duckdb
from fsspec import filesystem
from src.CustomTokenCredentialHelper import CustomTokenCredential
from src.ConvertToDQDataType import DQDataType
from src.validators import SourceValidators

class ADLSGen2Request(BaseModel):
    account_url: str = Field(..., description="Storage account URL name must be provided")
    # Example - 
    #https://synapseadlszonedeveus01.z39.dfs.storage.azure.net/
    #https://synapseadlszonedeveus01.z39.blob.storage.azure.net/
    #https://adlsdeveus02.blob.core.windows.net/
    #https://adlsdeveus02.dfs.core.windows.net/
    token: str = Field(..., description="Token must be provided")
    expires_on: int = Field(..., description="Token Expiration must be provided")

    @field_validator("account_url", mode="before")
    def validate_url(cls, value):
        return SourceValidators.validate_account_url(value)

    @field_validator('account_url','token')
    def check_not_empty(cls, value):
        return SourceValidators.not_empty(value)
    
    @field_validator('expires_on')
    def check_expires_on(cls,value):
        return SourceValidators.validate_expires_on(value)

    def test_connection(account_url: str, token:str,expires_on:int) -> Dict[str, str]:
        try:
            # Initialize ADLS client
            credential = CustomTokenCredential(token=token,expires_on=expires_on)
            service_client = DataLakeServiceClient(account_url=account_url, credential=credential)

            # Check if the filesystem are listable
            filesystems = service_client.list_file_systems()
            for _ in filesystems:  # Iterate through filesystems to ensure the API call succeeds
                break
            return {"status": "success", "result": "Connection successful"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

class ADLSGen2DeltaSchemaRequest(BaseModel):
    account_name: str = Field(..., description="Storage account name must be provided") #storageaccountname
    file_system_name: str = Field(..., description="File System Name must be provided") #mycontainer
    directory_path: str = Field(..., description="Directory Path must be provided")  #"someDeltapath/mytable"
    token: str = Field(..., description="Token must be provided")
    expires_on: int = Field(..., description="Token Expiration must be provided")

    @field_validator("account_name", mode="before")
    def validate_url(cls, value):
        return SourceValidators.validate_storage_account_name(value)

    @field_validator("file_system_name", mode="before")
    def validate_url(cls, value):
        return SourceValidators.validate_container_name(value)

    @field_validator('account_name', 'file_system_name', 'directory_path','token')
    def check_not_empty(cls, value):
        return SourceValidators.not_empty(value)
    
    @field_validator('expires_on')
    def check_expires_on(cls,value):
        return SourceValidators.validate_expires_on(value)

    def get_table_schema(account_name: str, file_system_name: str, directory_path: str,token:str,expires_on:int) -> Dict[str, List[Dict[str, str]]]:
        try:
            #credential = DefaultAzureCredential()
            #credential = CustomTokenCredential(token=token,expires_on=expires_on)
            storage_options={"bearer_token": token, "use_fabric_endpoint": "false"}
            #fs = AzureBlobFileSystem(account_name=account_name, credential=credential)
            arrow_table = DeltaTable(
                f"abfss://{file_system_name}@{account_name}.dfs.core.windows.net/{directory_path}",
                storage_options=storage_options
            ).schema().fields
            schema_list = [{"column_name": field.name, "dtype": str(field.type.type)} for field in arrow_table]
            # Fetch schema
            schema = DQDataType().fnconvertToDQDataType(schema_list=schema_list,sourceType="delta")
            return schema
        except Exception as e:
            return {"status": "error", "message": str(e)}

class ADLSGen2IcebergSchemaRequest(BaseModel):
    account_name: str = Field(..., description="Storage account name must be provided") #storageaccountname
    file_system_name: str = Field(..., description="File System Name must be provided") #mycontainer
    directory_path: str = Field(..., description="Directory Path must be provided")  #"someDeltapath/mytable"
    token: str = Field(..., description="Token must be provided")
    expires_on: int = Field(..., description="Token Expiration must be provided")

    @field_validator("account_name", mode="before")
    def validate_url(cls, value):
        return SourceValidators.validate_storage_account_name(value)

    @field_validator("file_system_name", mode="before")
    def validate_url(cls, value):
        return SourceValidators.validate_container_name(value)

    @field_validator('account_name', 'file_system_name', 'directory_path','token')
    def check_not_empty(cls, value):
        return SourceValidators.not_empty(value)

    @field_validator('expires_on')
    def check_expires_on(cls,value):
        return SourceValidators.validate_expires_on(value)


    def get_table_schema(account_name: str, file_system_name: str, directory_path: str,token:str,expires_on:int) -> Dict[str, List[Dict[str, str]]]:
        try:
            #credential = DefaultAzureCredential()
            credential = CustomTokenCredential(token=token,expires_on=expires_on)
            fs = filesystem("abfs", account_name=account_name, credential=credential)
            conn = duckdb.connect()
            try:
                conn.register_filesystem(fs)
                conn.sql("INSTALL iceberg; LOAD iceberg;")
                schema_result = conn.sql(
                    f"DESCRIBE (SELECT * FROM iceberg_scan('abfs://{file_system_name}@{account_name}.dfs.core.windows.net/{directory_path}', allow_moved_paths=true) LIMIT 1)"
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

class ADLSGen2ParquetSchemaRequest(BaseModel):
    account_name: str = Field(..., description="Storage account name must be provided") #storageaccountname
    file_system_name: str = Field(..., description="File System Name must be provided") #mycontainer
    directory_path: str = Field(..., description="Directory Path must be provided")  #"someDeltapath/mytable"
    token: str = Field(..., description="Token must be provided")
    expires_on: int = Field(..., description="Token Expiration must be provided")    
    
    @field_validator("account_name", mode="before")
    def validate_url(cls, value):
        return SourceValidators.validate_storage_account_name(value)

    @field_validator("file_system_name", mode="before")
    def validate_url(cls, value):
        return SourceValidators.validate_container_name(value)

    @field_validator('account_name', 'file_system_name', 'directory_path','token')
    def check_not_empty(cls, value):
        return SourceValidators.not_empty(value)

    @field_validator('expires_on')
    def check_expires_on(cls,value):
        return SourceValidators.validate_expires_on(value)


    def get_table_schema(account_name, file_system_name, directory_path,token:str,expires_on:int):
        #credential = DefaultAzureCredential()
        credential = CustomTokenCredential(token=token,expires_on=expires_on)
        try:
            handler = pyarrowfs_adlgen2.AccountHandler.from_account_name(account_name, credential=credential)
            fs = pyarrow.fs.PyFileSystem(handler)
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
        

class ADLSGen2FormatDetector(BaseModel):
    account_name: str = Field(..., description="Storage account name must be provided") #storageaccountname
    file_system_name: str = Field(..., description="File System Name must be provided") #mycontainer
    directory_path: str = Field(..., description="Directory Path must be provided")  #"someDeltapath/mytable"
    token: str = Field(..., description="Token must be provided")
    expires_on: int = Field(..., description="Token Expiration must be provided")    
    
    @field_validator("account_name", mode="before")
    def validate_url(cls, value):
        return SourceValidators.validate_storage_account_name(value)

    @field_validator("file_system_name", mode="before")
    def validate_url(cls, value):
        return SourceValidators.validate_container_name(value)

    @field_validator('account_name', 'file_system_name', 'directory_path','token')
    def check_not_empty(cls, value):
        return SourceValidators.not_empty(value)
    
    @field_validator('expires_on')
    def check_expires_on(cls,value):
        return SourceValidators.validate_expires_on(value)


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
                fs = filesystem("abfs", account_name=account_name, credential=credential)
                conn = duckdb.connect()
                try:
                    conn.register_filesystem(fs)
                    conn.sql("INSTALL iceberg; LOAD iceberg;")
                    result = conn.sql(
                        f"DESCRIBE (SELECT * FROM iceberg_scan('abfs://{file_system_name}@{account_name}.dfs.core.windows.net/{directory_path}', allow_moved_paths=true) LIMIT 1)"
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
                storage_options={"bearer_token": token, "use_fabric_endpoint": "false"}
                #fs = AzureBlobFileSystem(account_name=account_name, credential=credential)
                delta_table = DeltaTable(f"abfss://{file_system_name}@{account_name}.dfs.core.windows.net/{directory_path}", storage_options=storage_options)
                # If no error, it's a Delta format
                return {"status": "success", "format": "delta" }
            except Exception:
                # Not a Delta format, proceed to check for Parquet
                pass
            # Try to detect Parquet format
            try:
                # Attempt to read the directory as a Parquet dataset
                handler = pyarrowfs_adlgen2.AccountHandler.from_account_name(account_name, credential=credential)
                fs = pyarrow.fs.PyFileSystem(handler)
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
            handler = pyarrowfs_adlgen2.AccountHandler.from_account_name(account_name, credential=credential)
            fs = pyarrow.fs.PyFileSystem(handler)
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