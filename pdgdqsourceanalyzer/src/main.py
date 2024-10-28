# Import Uvicorn & the necessary modules from FastAPI
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from dotenv import load_dotenv
import asyncio
import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from starlette.status import HTTP_408_REQUEST_TIMEOUT, HTTP_504_GATEWAY_TIMEOUT
from pydantic import BaseModel
import pyodbc
from src.DatabricksUnityCatalog import DatabricksUnityCatalogSchemaRequest, DatabricksUnityCatalogRequest
from src.Snowflakedw import SnowflakeDWRequest, SnowflakeDWSchemaRequest
from src.GoogleBigQuery import GoogleBigQueryRequest, GoogleBigQuerySchemaRequest
from src.ADLSGen2 import ADLSGen2Request,ADLSGen2DeltaSchemaRequest,ADLSGen2ParquetSchemaRequest,ADLSGen2IcebergSchemaRequest,ADLSGen2FormatDetector
from src.AzureSQL import AzureSQLRequest,AzureSQLSchemaRequest
from src.Fabric import FabricRequest, FabricDeltaSchemaRequest

# Load the environment variables from the .env file into the application
load_dotenv() 
# Initialize the FastAPI application
app = FastAPI()

# Define a list of allowed common names (CNs) for validation
ALLOWED_CN = ["cus.dataquality-service.purview.azure.com"]

# Middleware to enforce a request timeout of 30 seconds
@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    try:
        # Enforce a timeout of 30 seconds for each request
        return await asyncio.wait_for(call_next(request), timeout=30)
    except asyncio.TimeoutError:
        # Return 504 Gateway Timeout for requests exceeding the time limit
        return JSONResponse(
            status_code=HTTP_504_GATEWAY_TIMEOUT,
            content={"message": "Request took too long, please try again later."}
        )
    except Exception as e:
        # Catch other exceptions and return a 500 Internal Server Error
        return JSONResponse(
            status_code=500,
            content={"message": f"An unexpected error occurred: {str(e)}"}
        )

def verify_client_certificate(request: Request):
    client_cert_subject = request.scope["transport"].get_extra_info("ssl_object").getpeercert()["subject"]
    # Raise an HTTP 403 Forbidden error if no valid client certificate is presented
    for item in client_cert_subject:
        if item[0][0] == 'commonName':
            client_cert_subjec_name = item[0][1]
            break
    if client_cert_subjec_name not in ALLOWED_CN:
        print("Invalid client cert subject -", client_cert_subject)
        raise HTTPException(status_code=403, detail="Valid Client certificate is required.")

@app.get("/test")
async def test_hello_world():
    try:
        result = {"status": "success", "details": "Hello World"}
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

# Create the POST endpoint
@app.post("/databricksunitycatalog/testconnection")
async def test_databricksUnityCatalog_connection(connection_request: DatabricksUnityCatalogRequest):
    #verify_client_certificate(request)
    try:
        result = connection_request.test_connection()
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/databricksunitycatalog/getschema")
async def get_databricksUnityCatalog_schema(schema_request: DatabricksUnityCatalogSchemaRequest):
    #verify_client_certificate(request)
    try:
        result = schema_request.get_table_schema()
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/snowflake/testconnection")
async def test_snowflake_connection(connection_request: SnowflakeDWRequest):
    #verify_client_certificate(request)
    try:
        result = connection_request.test_connection()
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/snowflake/getschema")
async def get_snowflake_schema(schema_request: SnowflakeDWSchemaRequest):
    #verify_client_certificate(request)
    try:
        result = schema_request.get_table_schema()
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

# New Google BigQuery endpoints
@app.post("/googlebigquery/testconnection")
async def test_googleBigQuery_connection(connection_request: GoogleBigQueryRequest):
    #verify_client_certificate(request)
    try:
        result = connection_request.test_connection()
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/googlebigquery/getschema")
async def get_googleBigQuery_schema(schema_request: GoogleBigQuerySchemaRequest):
    #verify_client_certificate(request)
    try:
        result = schema_request.get_table_schema()
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

# ADLS Gen2 endpoints
@app.post("/adlsgen2/testconnection")
async def test_adlsgen2_connection(connection_request: ADLSGen2Request):
    #verify_client_certificate(request)
    try:
        result = ADLSGen2Request.test_connection(
            connection_request.account_name,
            connection_request.file_system_name,
            connection_request.directory_path,
            connection_request.token,
            connection_request.expires_on,
            connection_request.storage_type
        )
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/adlsgen2/getdeltaschema")
async def get_adlsgen2_schema(schema_request: ADLSGen2DeltaSchemaRequest):
    #verify_client_certificate(request)
    try:
        result = ADLSGen2DeltaSchemaRequest.get_table_schema(
            schema_request.account_name,
            schema_request.file_system_name,
            schema_request.directory_path,
            schema_request.token,
            schema_request.expires_on
        )
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/adlsgen2/getparquetschema")
async def get_adlsgen2_schema(schema_request: ADLSGen2ParquetSchemaRequest):
    #verify_client_certificate(request)
    try:
        result = ADLSGen2ParquetSchemaRequest.get_table_schema(
            schema_request.account_name,
            schema_request.file_system_name,
            schema_request.directory_path,
            schema_request.token,
            schema_request.expires_on
        )
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/adlsgen2/geticebergschema")
async def get_adlsgen2_schema(schema_request: ADLSGen2IcebergSchemaRequest):
    #verify_client_certificate(request)
    try:
        result = ADLSGen2IcebergSchemaRequest.get_table_schema(
            schema_request.account_name,
            schema_request.file_system_name,
            schema_request.directory_path,
            schema_request.token,
            schema_request.expires_on
        )
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/adlsgen2/getformat")
async def get_adlsgen2_format(schema_request: ADLSGen2FormatDetector):
    #verify_client_certificate(request)
    try:
        result = ADLSGen2FormatDetector.detect_format(
            schema_request.account_name,
            schema_request.file_system_name,
            schema_request.directory_path,
            schema_request.token,
            schema_request.expires_on
        )
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/adlsgen2/getparquetpartitioncolumns")
async def get_adlsgen2_getPartitionColumns(schema_request: ADLSGen2FormatDetector):
    #verify_client_certificate(request)
    try:
        result = ADLSGen2FormatDetector.detect_partitions(
            schema_request.account_name,
            schema_request.file_system_name,
            schema_request.directory_path,
            schema_request.token,
            schema_request.expires_on
        )
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")


# Azure SQL Database endpoints
@app.post("/azuresql/testconnection")
async def test_azure_sql_connection(connection_request: AzureSQLRequest):
    #verify_client_certificate(request)
    try:
        result = connection_request.test_connection()
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/azuresql/getschema")
async def get_azure_sql_schema(schema_request: AzureSQLSchemaRequest):
    #verify_client_certificate(request)
    try:
        result = schema_request.get_table_schema()
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/fabric/testconnection")
async def test_fabric_connection(connection_request: FabricRequest):
    #verify_client_certificate(request)
    try:
        result = FabricRequest.test_connection(
            connection_request.account_name,
            connection_request.file_system_name,
            connection_request.directory_path,
            connection_request.token,
            connection_request.expires_on
        )
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/fabric/getdeltaschema")
async def get_fabric_schema(schema_request: FabricDeltaSchemaRequest):
    #verify_client_certificate(request)
    try:
        result = FabricDeltaSchemaRequest.get_table_schema(
            schema_request.account_name,
            schema_request.file_system_name,
            schema_request.directory_path,
            schema_request.token,
            schema_request.expires_on
        )
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")


if __name__ == '__main__':
    app.run(debug=True)