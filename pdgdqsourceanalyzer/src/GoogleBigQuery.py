from google.cloud import bigquery
from google.oauth2 import service_account
from pydantic import BaseModel, Field, field_validator
import json

class GoogleBigQueryRequest(BaseModel):
    credentials_json: str = Field(..., description="Service Account Credentials must be provided") # JSON string of the service account credentials
    
    @field_validator('credentials_json')
    def field_not_empty(cls, value):
        if not value:
            raise ValueError('Field cannot be empty')
        return value

    def test_connection(self):
        """
        Test connection to Google BigQuery.

        Returns:
            dict: Status and list of available datasets.
        """
        try:
            # Load credentials from the JSON string
            credentials = service_account.Credentials.from_service_account_info(json.loads(self.credentials_json))
            client = bigquery.Client(credentials=credentials)

            # Fetch datasets in the project
            datasets = list(client.list_datasets())
            dataset_names = [dataset.dataset_id for dataset in datasets]

            return {"status": "success", "datasets": dataset_names}

        except Exception as e:
            return {"status": "error", "message": str(e)}

class GoogleBigQuerySchemaRequest(BaseModel):
    credentials_json: str = Field(..., description="Service Account Credentials must be provided") # JSON string of the service account credentials
    project_id: str = Field(..., description="Project Id must be provided")
    dataset_id: str = Field(..., description="Dataset Id Credentials must be provided")
    table_id: str = Field(..., description="Table Name must be provided")
    
    @field_validator('credentials_json','project_id','dataset_id','table_id')
    def field_not_empty(cls, value):
        if not value:
            raise ValueError('Field cannot be empty')
        return value

    def get_table_schema(self):
        """
        Get the schema of a specific table in Google BigQuery.

        Returns:
            dict: Status and table schema details.
        """
        try:
            # Load credentials from the JSON string
            credentials = service_account.Credentials.from_service_account_info(json.loads(self.credentials_json))
            client = bigquery.Client(credentials=credentials, project=self.project_id)

            # Get table reference and fetch the table
            table_ref = f"{self.project_id}.{self.dataset_id}.{self.table_id}"
            table = client.get_table(table_ref)

            # Extract schema information (field names and types)
            schema_info = [{"name": field.name, "type": field.field_type} for field in table.schema]

            return {"status": "success", "schema": schema_info}

        except Exception as e:
            return {"status": "error", "message": str(e)}