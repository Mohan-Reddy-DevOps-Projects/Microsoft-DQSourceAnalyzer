from pydantic import BaseModel, Field, field_validator
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.storage.filedatalake import DataLakeServiceClient
from typing import List, Dict
from deltalake import DeltaTable
import pyarrow.parquet as pq
from azure.storage.filedatalake import DataLakeServiceClient
import pyarrow.dataset as ds
from fsspec import filesystem
from src.CustomTokenCredentialHelper import CustomTokenCredential

class FabricRequest(BaseModel):
    account_name: str = Field(..., description="Storage account name must be provided")
    file_system_name: str = Field(..., description="File System Name must be provided")
    directory_path: str = Field(..., description="Directory Path must be provided")
    token: str = Field(..., description="Token must be provided")
    expires_on: int = Field(..., description="Token Expiration must be provided")
    
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
            return {"status": "success", "message": "Connection successful"}
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
            storage_options={"bearer_token": token, "use_fabric_endpoint": "false"}
            arrow_table = DeltaTable(
                f"abfss://{file_system_name}@{account_name}.dfs.fabric.microsoft.com/{directory_path}",
                storage_options=storage_options
            ).schema().fields
            schema_list = [{"column_name": field.name, "dtype": str(field.type.type)} for field in arrow_table]
            # Fetch schema
            return {"status": "success", "schema": schema_list}
        except Exception as e:
            return {"status": "error", "message": str(e)}
