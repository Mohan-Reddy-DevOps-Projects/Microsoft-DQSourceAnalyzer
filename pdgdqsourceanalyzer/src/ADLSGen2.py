from pydantic import BaseModel
from azure.identity import DefaultAzureCredential
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

class ADLSGen2Request(BaseModel):
    account_name: str
    file_system_name: str
    directory_path: str

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
    account_name: str      #storageaccountname
    file_system_name: str  #mycontainer
    directory_path: str  #"someDeltapath/mytable"

    def get_table_schema(account_name: str, file_system_name: str, directory_path: str) -> Dict[str, List[Dict[str, str]]]:
        try:
            fs = AzureBlobFileSystem(account_name=account_name, credential=DefaultAzureCredential())
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

class ADLSGen2ParquetSchemaRequest(BaseModel):
    account_name: str      #storageaccountname
    file_system_name: str  #mycontainer
    directory_path: str  #"someDeltapath/mytable"    
    def get_table_schema(account_name, file_system_name, directory_path):
        credential = DefaultAzureCredential()
        try:
            azfs = AzureBlobFileSystem(account_name=account_name, 
                                    container_name=file_system_name, 
                                    credential=credential)
        
            adls_dir_path = f"{file_system_name}/{directory_path}"
            all_paths = azfs.find(adls_dir_path)
            first_parquet_file = None
            for file_path in all_paths:
                if file_path.endswith(".parquet"):
                    first_parquet_file = file_path
                    break  # Stop searching as soon as the first Parquet file is found

            if not first_parquet_file:
                return({"status": "error", "message": "No Parquet files found in the specified directory"})

            handler=pyarrowfs_adlgen2.AccountHandler.from_account_name(account_name,credential=credential)
            fs = pyarrow.fs.PyFileSystem(handler)
            with fs.open_input_file(first_parquet_file) as file:
                    parquet_schema = pq.read_schema(file)
            # Extract schema as a list of dictionaries
            schema_list = [{"column_name": field.name, "dtype": str(field.type)} for field in parquet_schema]
            # Return the schema
            return {"status": "success", "schema": schema_list}

        except Exception as e:
            return {"status": "error", "message": str(e)}