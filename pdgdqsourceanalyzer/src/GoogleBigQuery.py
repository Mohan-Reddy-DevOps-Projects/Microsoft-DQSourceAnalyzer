from google.cloud import bigquery
from google.oauth2 import service_account
from pydantic import BaseModel
import json

class GoogleBigQueryRequest(BaseModel):
    credentials_json: str  # JSON string of the service account credentials

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
    credentials_json: str  # JSON string of the service account credentials
    project_id: str
    dataset_id: str
    table_id: str

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