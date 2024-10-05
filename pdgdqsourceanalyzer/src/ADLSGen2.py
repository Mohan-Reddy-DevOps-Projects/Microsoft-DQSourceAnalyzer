from pydantic import BaseModel, Field, field_validator
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.storage.filedatalake import DataLakeServiceClient
from typing import List, Dict
from adlfs import AzureBlobFileSystem
from deltalake import DeltaTable
import json,os
import pyarrow.parquet as pq
from azure.storage.filedatalake import DataLakeServiceClient
from azure.identity import DefaultAzureCredential
import pyarrowfs_adlgen2
import pyarrow
import pyarrow.dataset as ds

class ADLSGen2Request(BaseModel):
    account_name: str = Field(..., description="Storage account name must be provided")
    file_system_name: str = Field(..., description="File System Name must be provided")
    directory_path: str = Field(..., description="Directory Path must be provided")
    
    @field_validator('account_name', 'file_system_name', 'directory_path')
    def field_not_empty(cls, value):
        if not value:
            raise ValueError('Field cannot be empty')
        return value

    def test_connection(account_name: str, file_system_name: str, directory_path: str) -> Dict[str, str]:
        try:
            # Initialize ADLS client
            credential = DefaultAzureCredential()
            account_url = f"https://{account_name}.dfs.core.windows.net"
            service_client = DataLakeServiceClient(account_url=account_url, credential=credential)

            # Check if the directory exists
            file_system_client = service_client.get_file_system_client(file_system=file_system_name)
            directory_client = file_system_client.get_directory_client(directory_path)
            if not directory_client.exists():
                return {"status": "error", "message": "Directory does not exist"}

            return {"status": "success", "message": "Connection successful"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

class ADLSGen2DeltaSchemaRequest(BaseModel):
    account_name: str = Field(..., description="Storage account name must be provided") #storageaccountname
    file_system_name: str = Field(..., description="File System Name must be provided") #mycontainer
    directory_path: str = Field(..., description="Directory Path must be provided")  #"someDeltapath/mytable"
    
    @field_validator('account_name', 'file_system_name', 'directory_path')
    def field_not_empty(cls, value):
        if not value:
            raise ValueError('Field cannot be empty')
        return value

    def get_table_schema(account_name: str, file_system_name: str, directory_path: str) -> Dict[str, List[Dict[str, str]]]:
        try:
            credential = DefaultAzureCredential()
            fs = AzureBlobFileSystem(account_name=account_name, credential=credential)
            # Use delta-lake-reader to access the table schema
            arrow_table = DeltaTable(
                f"{file_system_name}/{directory_path}",
                file_system=fs
            ).schema
            schema_list = [{"column_name": field.name, "dtype": str(field.type)} for field in arrow_table]
            # Fetch schema
            return {"status": "success", "schema": schema_list}
        except Exception as e:
            return {"status": "error", "message": str(e)}

class ADLSGen2IcebergSchemaRequest(BaseModel):
    account_name: str = Field(..., description="Storage account name must be provided") #storageaccountname
    file_system_name: str = Field(..., description="File System Name must be provided") #mycontainer
    directory_path: str = Field(..., description="Directory Path must be provided")  #"someDeltapath/mytable"
    
    @field_validator('account_name', 'file_system_name', 'directory_path')
    def field_not_empty(cls, value):
        if not value:
            raise ValueError('Field cannot be empty')
        return value

    def get_table_schema(account_name: str, file_system_name: str, directory_path: str) -> Dict[str, List[Dict[str, str]]]:
        try:

            credential = DefaultAzureCredential()
            fs = AzureBlobFileSystem(account_name=account_name, credential=credential)
            table_metadata_root_path = f"abfss://{file_system_name}@{account_name}.dfs.core.windows.net/{directory_path}/metadata"
            metadata_files = fs.ls(table_metadata_root_path)
            # Find the latest metadata file, assuming they are named "v1.metadata.json", "v2.metadata.json", etc.
            # Sort the files to ensure we pick the latest version
            metadata_files = sorted([f for f in metadata_files if f.endswith(".metadata.json")], reverse=True)
            latest_metadata_path = metadata_files[0] if metadata_files else None
            if latest_metadata_path:
                # Step 2: Read the latest metadata file
                with fs.open(latest_metadata_path, 'rb') as metadata_file:
                    metadata_json = json.load(metadata_file)
                # Step 3: Inspect the schema and partitions
                schema = metadata_json.get('schema', {})
                schema_list = [{"column_name": field.get('name'), "dtype":field.get('type')} for field in schema.get('fields', [])]
            # Fetch schema
            return {"status": "success", "schema": schema_list}
        except Exception as e:
            return {"status": "error", "message": str(e)}

class ADLSGen2ParquetSchemaRequest(BaseModel):
    account_name: str = Field(..., description="Storage account name must be provided") #storageaccountname
    file_system_name: str = Field(..., description="File System Name must be provided") #mycontainer
    directory_path: str = Field(..., description="Directory Path must be provided")  #"someDeltapath/mytable"
    
    @field_validator('account_name', 'file_system_name', 'directory_path')
    def field_not_empty(cls, value):
        if not value:
            raise ValueError('Field cannot be empty')
        return value
        
    def get_table_schema(account_name, file_system_name, directory_path):
        credential = DefaultAzureCredential()
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
                return {"status": "success", "schema": schema_list}
        
        except Exception as e:
            return {"status": "error", "message": str(e)}
        

class ADLSGen2FormatDetector(BaseModel):
    account_name: str = Field(..., description="Storage account name must be provided") #storageaccountname
    file_system_name: str = Field(..., description="File System Name must be provided") #mycontainer
    directory_path: str = Field(..., description="Directory Path must be provided")  #"someDeltapath/mytable"
    
    @field_validator('account_name', 'file_system_name', 'directory_path')
    def field_not_empty(cls, value):
        if not value:
            raise ValueError('Field cannot be empty')
        return value

    def detect_format(account_name, file_system_name, directory_path) -> str:
        """
        Detect the format of the directory (Delta or Parquet) on ADLS Gen2.
        Returns:
            - "iceberg":If the directory is in Iceberg format.
            - "delta": If the directory is in Delta format.
            - "parquet": If the directory is in Parquet format.
            - "unsupportedFormat": If neither format is detected.
        """
        try:
            credential = DefaultAzureCredential()
            full_path = f"{file_system_name}/{directory_path}"
            # Try to detect Iceberg format
            metadata_dir = f"{full_path}/metadata"
            data_dir = f"{full_path}/data"
            fs = AzureBlobFileSystem(account_name=account_name, credential=credential)
            try:
                # Check if the metadata and data directory exists
                if fs.exists(metadata_dir) and fs.exists(data_dir):
                    # List metadata files in the directory
                    metadata_files = fs.ls(metadata_dir)
                    # Check for Iceberg metadata files (v1.metadata.json, v2.metadata.json, etc.)
                    iceberg_metadata_files = [f for f in metadata_files if f.endswith(".metadata.json")]
                    if iceberg_metadata_files:
                        print(f"Iceberg metadata files found: {iceberg_metadata_files}")
                        return {"status": "success", "format": "iceberg" }
            except Exception:
                # Not a Iceberg format, proceed to check for Delta Format
                pass
            # Try to detect Delta format
            try:
                delta_table = DeltaTable(full_path, file_system=fs)
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

    def detect_partitions(account_name, file_system_name, directory_path) -> str:
        """
        Detect if the (Iceberg or Delta or Parquet) directory on ADLS Gen2 is partitioned.
        Returns:
            - "isPartitioned": True - if partitioned else False
            - "partitionedColumns": Returns Partitioned Columns, else []
        """
        try:
            
            isPartitioned = False
            partition_columns = []
            credential = DefaultAzureCredential()
            full_path = f"{file_system_name}/{directory_path}"
            # Try to detect Iceberg format
            metadata_dir = f"{full_path}/metadata"
            data_dir = f"{full_path}/data"
            fs = AzureBlobFileSystem(account_name=account_name, credential=credential)
            # Check if the metadata and data directory exists
            if fs.exists(metadata_dir) and fs.exists(data_dir):
                # List metadata files in the directory
                metadata_files = fs.ls(metadata_dir)
                # Check for Iceberg metadata files (v1.metadata.json, v2.metadata.json, etc.)
                iceberg_metadata_files = [f for f in metadata_files if f.endswith(".metadata.json")]
                if iceberg_metadata_files:
                    table_metadata_root_path = f"abfss://{file_system_name}@{account_name}.dfs.core.windows.net/{directory_path}/metadata"
                    metadata_files = fs.ls(table_metadata_root_path)
                    # Find the latest metadata file, assuming they are named "v1.metadata.json", "v2.metadata.json", etc.
                    # Sort the files to ensure we pick the latest version
                    metadata_files = sorted([f for f in metadata_files if f.endswith(".metadata.json")], reverse=True)
                    latest_metadata_path = metadata_files[0] if metadata_files else None
                    if latest_metadata_path:
                        # Step 2: Read the latest metadata file
                        with fs.open(latest_metadata_path, 'rb') as metadata_file:
                            metadata_json = json.load(metadata_file)
                        # Step 3: Inspect the schema and partitions
                        schema = metadata_json.get('schema', {})
                        partitions = metadata_json.get('partition-spec', [])
                        if partitions:
                            isPartitioned = True
                            partition_columns = [
                                                    {
                                                        "column_name": field.get('name'),
                                                        "dtype": next(
                                                            (schema_field['type'] for schema_field in schema.get('fields', []) 
                                                            if schema_field['name'] == field.get('name')), 
                                                            None
                                                        )
                                                    } 
                                                    for field in partitions
                                                ]
                    return {"status": "success", "isPartitioned": isPartitioned,"partition_columns":partition_columns}
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