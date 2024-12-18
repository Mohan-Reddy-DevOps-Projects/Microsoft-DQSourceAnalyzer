import requests
from pydantic import BaseModel, Field, field_validator
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from typing import List, Dict
import json,os
from src.CustomTokenCredentialHelper import CustomTokenCredential

class PowerBIRequest(BaseModel):
    tenantId: str = Field(..., description="TenantId must be provided")
    token: str = Field(..., description="Token must be provided")
    expires_on: int = Field(..., description="Token Expiration must be provided")
    
    @field_validator('tenantId', 'token','expires_on')
    def field_not_empty(cls, value):
        if not value:
            raise ValueError('Field cannot be empty')
        return value

    def test_connection(tenantId: str, token: str, expires_on: int) -> Dict[str, str]:
        try:
            #Token Audience
            #token = credential.get_token("https://analysis.windows.net/powerbi/api/.default")
            #token = credential.get_token("https://api.fabric.microsoft.com/.default")

            #POWER_BI_API_ENDPOINT = "https://api.powerbi.com/v1.0/myorg/groups"
            FABRIC_WORKSPACES_API = "https://api.fabric.microsoft.com/v1/workspaces"
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(FABRIC_WORKSPACES_API, headers=headers)

            if response.status_code == 200:
                response_json = response.json()
                workspaces = [
                                {"workspaceId": item["id"], "workspaceName": item["displayName"]}
                                for item in response_json.get("value", [])
                                if item.get("type") == "Workspace"
                                ]
                return {"status": "success", "result": workspaces}
                ## Example {'status': 'success', 'result': [{'workspaceId': 'c4dd39bb-77e2-43d3-af10-712845dc2179', 'workspaceName': 'CorpBI'}, {'workspaceId': '86f9770b-23a7-4cf8-a877-51734a900e66', 'workspaceName': 'dq-workspace'}, {'workspaceId': 'c91b1a76-c8df-4f19-be51-41688eb5c0ea', 'workspaceName': 'Sustainability'}, {'workspaceId': 'd348f7cc-755b-4309-ab2c-505dc0c64726', 'workspaceName': 'corpbi-pdg07'}, {'workspaceId': '9fa24700-1a69-4ef0-88aa-3608e22db3d5', 'workspaceName': 'pdg07-dataactivator'}]}
            else:
                return {"status": "error", "message": f"Failed to connect to Fabric API. Status Code: {response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}