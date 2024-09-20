# Import Uvicorn & the necessary modules from FastAPI
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from dotenv import load_dotenv
import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pyodbc
from src.DatabricksUnityCatalog import DatabricksUnityCatalogSchemaRequest, DatabricksUnityCatalogRequest
from src.Snowflakedw import SnowflakeDWRequest, SnowflakeDWSchemaRequest
from src.GoogleBigQuery import GoogleBigQueryRequest, GoogleBigQuerySchemaRequest
from src.ADLSGen2 import ADLSGen2Request,ADLSGen2DeltaSchemaRequest,ADLSGen2ParquetSchemaRequest,ADLSGen2FormatDetector
from src.AzureSQL import AzureSQLRequest,AzureSQLSchemaRequest
# Load the environment variables from the .env file into the application
load_dotenv() 
# Initialize the FastAPI application
app = FastAPI()

# Create the POST endpoint
@app.post("/databricksUnityCatalog-testconnection")
async def test_databricksUnityCatalog_connection(connection_request: DatabricksUnityCatalogRequest):
    result = DatabricksUnityCatalogRequest.test_connection(
        connection_request.hostname,
        connection_request.http_path,
        connection_request.access_token
    )
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@app.post("/databricksUnityCatalog-getschema")
async def get_databricksUnityCatalog_schema(schema_request: DatabricksUnityCatalogSchemaRequest):
    result = DatabricksUnityCatalogSchemaRequest.get_table_schema(
        schema_request.hostname,
        schema_request.http_path,
        schema_request.access_token,
        schema_request.catalog,
        schema_request.unitycatalogschema,
        schema_request.table
    )
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.post("/snowflake-testconnection")
async def test_snowflake_connection(connection_request: SnowflakeDWRequest):
    result = SnowflakeDWRequest.test_connection(
        connection_request.account,
        connection_request.user,
        connection_request.password,
        connection_request.warehouse,
        connection_request.database,
        connection_request.snowflakeschema
    )
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.post("/snowflake-getschema")
async def get_snowflake_schema(schema_request: SnowflakeDWSchemaRequest):
    result = SnowflakeDWSchemaRequest.get_table_schema(
        schema_request.account,
        schema_request.user,
        schema_request.password,
        schema_request.warehouse,
        schema_request.database,
        schema_request.snowflakeschema,
        schema_request.table
    )
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

# New Google BigQuery endpoints
@app.post("/googleBigQuery-testconnection")
async def test_googleBigQuery_connection(connection_request: GoogleBigQueryRequest):
    result = connection_request.test_connection()
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.post("/googleBigQuery-getschema")
async def get_googleBigQuery_schema(schema_request: GoogleBigQuerySchemaRequest):
    result = schema_request.get_table_schema()
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

# ADLS Gen2 endpoints
@app.post("/adlsgen2-testconnection")
async def test_adlsgen2_connection(connection_request: ADLSGen2Request):
    result = ADLSGen2Request.test_connection(
        connection_request.account_name,
        connection_request.file_system_name,
        connection_request.directory_path
    )
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.post("/adlsgen2-getschema")
async def get_adlsgen2_schema(schema_request: ADLSGen2DeltaSchemaRequest):
    result = ADLSGen2DeltaSchemaRequest.get_table_schema(
        schema_request.account_name,
        schema_request.file_system_name,
        schema_request.directory_path
    )
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.post("/adlsgen2-getparquetschema")
async def get_adlsgen2_schema(schema_request: ADLSGen2ParquetSchemaRequest):
    result = ADLSGen2ParquetSchemaRequest.get_table_schema(
        schema_request.account_name,
        schema_request.file_system_name,
        schema_request.directory_path
    )
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.post("/adlsgen2-getFormat")
async def get_adlsgen2_format(schema_request: ADLSGen2FormatDetector):
    result = ADLSGen2FormatDetector.detect_format(
        schema_request.account_name,
        schema_request.file_system_name,
        schema_request.directory_path
    )
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

# Azure SQL Database endpoints
@app.post("/azure-sql-testconnection")
async def test_azure_sql_connection(connection_request: AzureSQLRequest):
    result = AzureSQLRequest.test_connection(
        connection_request.server,
        connection_request.database
    )
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.post("/azure-sql-getschema")
async def get_azure_sql_schema(schema_request: AzureSQLSchemaRequest):
    result = AzureSQLSchemaRequest.get_table_schema(
        schema_request.server,
        schema_request.database,
        schema_request.table
    )
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


if __name__ == '__main__':
    app.run(debug=True)