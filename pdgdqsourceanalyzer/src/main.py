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
from src.ADLSGen2 import ADLSGen2Request,ADLSGen2DeltaSchemaRequest,ADLSGen2ParquetSchemaRequest,ADLSGen2FormatDetector
from src.AzureSQL import AzureSQLRequest,AzureSQLSchemaRequest

# Load the environment variables from the .env file into the application
load_dotenv() 
# Initialize the FastAPI application
app = FastAPI()

# Middleware to enforce a request timeout of 20 seconds
@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    try:
        # Enforce a timeout of 100 seconds for each request
        return await asyncio.wait_for(call_next(request), timeout=20)
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

# Create the POST endpoint
@app.post("/databricksunitycatalog/testconnection")
async def test_databricksUnityCatalog_connection(connection_request: DatabricksUnityCatalogRequest):
    try:
        result = DatabricksUnityCatalogRequest.test_connection(
            connection_request.hostname,
            connection_request.http_path,
            connection_request.access_token
        )
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/databricksunitycatalog/getschema")
async def get_databricksUnityCatalog_schema(schema_request: DatabricksUnityCatalogSchemaRequest):
    try:
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
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/snowflake/testconnection")
async def test_snowflake_connection(connection_request: SnowflakeDWRequest):
    try:
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
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/snowflake/getschema")
async def get_snowflake_schema(schema_request: SnowflakeDWSchemaRequest):
    try:
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
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

# New Google BigQuery endpoints
@app.post("/googlebigquery/testconnection")
async def test_googleBigQuery_connection(connection_request: GoogleBigQueryRequest):
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
    try:
        result = ADLSGen2Request.test_connection(
            connection_request.account_name,
            connection_request.file_system_name,
            connection_request.directory_path
        )
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/adlsgen2/getschema")
async def get_adlsgen2_schema(schema_request: ADLSGen2DeltaSchemaRequest):
    try:
        result = ADLSGen2DeltaSchemaRequest.get_table_schema(
            schema_request.account_name,
            schema_request.file_system_name,
            schema_request.directory_path
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
    try:
        result = ADLSGen2ParquetSchemaRequest.get_table_schema(
            schema_request.account_name,
            schema_request.file_system_name,
            schema_request.directory_path
        )
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/adlsgen2/getFormat")
async def get_adlsgen2_format(schema_request: ADLSGen2FormatDetector):
    try:
        result = ADLSGen2FormatDetector.detect_format(
            schema_request.account_name,
            schema_request.file_system_name,
            schema_request.directory_path
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
    try:
        result = AzureSQLRequest.test_connection(
            connection_request.server,
            connection_request.database
        )
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/azuresql/getschema")
async def get_azure_sql_schema(schema_request: AzureSQLSchemaRequest):
    try:
        result = AzureSQLSchemaRequest.get_table_schema(
            schema_request.server,
            schema_request.database,
            schema_request.table
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