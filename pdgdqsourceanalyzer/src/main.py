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
from src.Fabric import FabricRequest, FabricDeltaSchemaRequest, FabricIcebergSchemaRequest, FabricParquetSchemaRequest, FabricFormatDetector
from src.PowerBI import PowerBIRequest
import logger

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(levelname)s - %(message)s",  # Log format
    handlers=[
        logging.StreamHandler(),  # Logs to console
        #logging.FileHandler("app.log"),  # Logs to a file named 'app.log'
    ]
)

logger = logging.getLogger(__name__)

# Load the environment variables from the .env file into the application
load_dotenv() 
# Initialize the FastAPI application
app = FastAPI()

# Define a list of allowed common names (CNs) for validation

ALLOWED_CN = ["weu.dataquality-service.purview.azure.com","ae.dataquality-service.purview.azure.com","brs.dataquality-service.purview.azure.com","cae.dataquality-service.purview.azure.com","cc.dataquality-service.purview.azure.com","cid.dataquality-service.purview.azure.com","dewc.dataquality-service.purview.azure.com","eus.dataquality-service.purview.azure.com","eus2.dataquality-service.purview.azure.com","fc.dataquality-service.purview.azure.com","jpe.dataquality-service.purview.azure.com","kc.dataquality-service.purview.azure.com","ne.dataquality-service.purview.azure.com","san.dataquality-service.purview.azure.com","sc.dataquality-service.purview.azure.com","scus.dataquality-service.purview.azure.com","sea.dataquality-service.purview.azure.com","stzn.dataquality-service.purview.azure.com","uks.dataquality-service.purview.azure.com","wcus.dataquality-service.purview.azure.com","wus.dataquality-service.purview.azure.com","wus2.dataquality-service.purview.azure.com","cus.dataquality-service.purview.azure.com","wus2.dataquality-service.purview.azure-test.com","uaen.dataquality-service.purview.azure.com"]

# Middleware to enforce a request timeout of 30 seconds
@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    try:
        body = await request.body()
        try:
            body_data = json.loads(body)
            sensitive_keys = ["token", "expires_on","user", "password", "credentials_json" ,"access_token"]
            redacted_body = redact_sensitive_data(body_data, sensitive_keys)
            redacted_body_str = json.dumps(redacted_body, indent=2)
        except json.JSONDecodeError:
            redacted_body_str = body.decode('utf-8')

        logger.info(f"Processing request: {request.method} {request.url}")
        logger.info(f"Request headers: {dict(request.headers)}")
        logger.info(f"Request payload: {redacted_body_str}")
        return await asyncio.wait_for(call_next(request), timeout=30)
    except asyncio.TimeoutError:
        # Return 504 Gateway Timeout for requests exceeding the time limit
        logger.error("Request timeout occurred.")
        return JSONResponse(
            status_code=HTTP_504_GATEWAY_TIMEOUT,
            content={"message": "Request took too long, please try again later."}
        )
    except Exception as e:
        # Catch other exceptions and return a 500 Internal Server Error
        logger.exception("An unexpected error occurred during request processing.")
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
        DQS_ENV_REGION = os.getenv('DQS_ENV_REGION','DEFAULT_DEV')
        result = {"status": "success", "details": f"Hello World ENV {DQS_ENV_REGION}"}
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

# Create the POST endpoint
@app.post("/databricksunitycatalog/testconnection")
async def test_databricksUnityCatalog_connection(request: Request, connection_request: DatabricksUnityCatalogRequest):
    verify_client_certificate(request)
    try:
        result = connection_request.test_connection()
        if result["status"] == "error":
            logger.error(f"Databricks UnityCatalog Connection test failed: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        logger.error(f"HTTP exception occurred: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("An unexpected error occurred.")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/databricksunitycatalog/getschema")
async def get_databricksUnityCatalog_schema(request: Request, schema_request: DatabricksUnityCatalogSchemaRequest):
    verify_client_certificate(request)
    try:
        result = schema_request.get_table_schema()
        if result["status"] == "error":
            logger.error(f"Databricks UnityCatalog GetSchema failed: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        logger.error(f"HTTP exception occurred: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("An unexpected error occurred.")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/snowflake/testconnection")
async def test_snowflake_connection(request: Request, connection_request: SnowflakeDWRequest):
    verify_client_certificate(request)
    try:
        result = connection_request.test_connection()
        if result["status"] == "error":
            logger.error(f"Snowflake Test Connection failed: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        logger.error(f"HTTP exception occurred: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("An unexpected error occurred.")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/snowflake/getschema")
async def get_snowflake_schema(request: Request, schema_request: SnowflakeDWSchemaRequest):
    verify_client_certificate(request)
    try:
        result = schema_request.get_table_schema()
        if result["status"] == "error":
            logger.error(f"Snowflake GetSchema failed: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        logger.error(f"HTTP exception occurred: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("An unexpected error occurred.")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

# New Google BigQuery endpoints
@app.post("/googlebigquery/testconnection")
async def test_googleBigQuery_connection(request: Request, connection_request: GoogleBigQueryRequest):
    verify_client_certificate(request)
    try:
        result = connection_request.test_connection()
        if result["status"] == "error":
            logger.error(f"Google BigQuery Test Connection failed: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        logger.error(f"HTTP exception occurred: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("An unexpected error occurred.")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/googlebigquery/getschema")
async def get_googleBigQuery_schema(request: Request, schema_request: GoogleBigQuerySchemaRequest):
    verify_client_certificate(request)
    try:
        result = schema_request.get_table_schema()
        if result["status"] == "error":
            logger.error(f"Google BigQuery GetSchema failed: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        logger.error(f"HTTP exception occurred: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("An unexpected error occurred.")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

# ADLS Gen2 endpoints
@app.post("/adlsgen2/testconnection")
async def test_adlsgen2_connection(request: Request, connection_request: ADLSGen2Request):
    verify_client_certificate(request)
    try:
        result = ADLSGen2Request.test_connection(
            connection_request.account_url,
            connection_request.token,
            connection_request.expires_on
        )
        if result["status"] == "error":
            logger.error(f"ADLS Gen2 Test Connection failed: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        logger.error(f"HTTP exception occurred: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("An unexpected error occurred.")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/adlsgen2/getdeltaschema")
async def get_adlsgen2_schema(request: Request, schema_request: ADLSGen2DeltaSchemaRequest):
    verify_client_certificate(request)
    try:
        result = ADLSGen2DeltaSchemaRequest.get_table_schema(
            schema_request.account_name,
            schema_request.file_system_name,
            schema_request.directory_path,
            schema_request.token,
            schema_request.expires_on
        )
        if result["status"] == "error":
            logger.error(f"ADLS Gen2 Get Delta Schema failed: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        logger.error(f"HTTP exception occurred: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("An unexpected error occurred.")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/adlsgen2/getparquetschema")
async def get_adlsgen2_schema(request: Request, schema_request: ADLSGen2ParquetSchemaRequest):
    verify_client_certificate(request)
    try:
        result = ADLSGen2ParquetSchemaRequest.get_table_schema(
            schema_request.account_name,
            schema_request.file_system_name,
            schema_request.directory_path,
            schema_request.token,
            schema_request.expires_on
        )
        if result["status"] == "error":
            logger.error(f"ADLS Gen2 Get Parquet Schema failed: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        logger.error(f"HTTP exception occurred: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("An unexpected error occurred.")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/adlsgen2/geticebergschema")
async def get_adlsgen2_schema(request: Request, schema_request: ADLSGen2IcebergSchemaRequest):
    verify_client_certificate(request)
    try:
        result = ADLSGen2IcebergSchemaRequest.get_table_schema(
            schema_request.account_name,
            schema_request.file_system_name,
            schema_request.directory_path,
            schema_request.token,
            schema_request.expires_on
        )
        if result["status"] == "error":
            logger.error(f"ADLS Gen2 Get Iceberg Schema failed: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        logger.error(f"HTTP exception occurred: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("An unexpected error occurred.")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/adlsgen2/getformat")
async def get_adlsgen2_format(request: Request, schema_request: ADLSGen2FormatDetector):
    verify_client_certificate(request)
    try:
        result = ADLSGen2FormatDetector.detect_format(
            schema_request.account_name,
            schema_request.file_system_name,
            schema_request.directory_path,
            schema_request.token,
            schema_request.expires_on
        )
        if result["status"] == "error":
            logger.error(f"ADLS Gen2 Format Detection failed: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        logger.error(f"HTTP exception occurred: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("An unexpected error occurred.")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/adlsgen2/getparquetpartitioncolumns")
async def get_adlsgen2_getPartitionColumns(request: Request, schema_request: ADLSGen2FormatDetector):
    verify_client_certificate(request)
    try:
        result = ADLSGen2FormatDetector.detect_partitions(
            schema_request.account_name,
            schema_request.file_system_name,
            schema_request.directory_path,
            schema_request.token,
            schema_request.expires_on
        )
        if result["status"] == "error":
            logger.error(f"ADLS Gen2 Parquet Partition Column Detection failed: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        logger.error(f"HTTP exception occurred: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("An unexpected error occurred.")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")


# Azure SQL Database endpoints
@app.post("/azuresql/testconnection")
async def test_azure_sql_connection(request: Request, connection_request: AzureSQLRequest):
    verify_client_certificate(request)
    try:
        result = connection_request.test_connection()
        if result["status"] == "error":
            logger.error(f"SQL DB Test Connection failed: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        logger.error(f"HTTP exception occurred: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("An unexpected error occurred.")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/azuresql/getschema")
async def get_azure_sql_schema(request: Request, schema_request: AzureSQLSchemaRequest):
    verify_client_certificate(request)
    try:
        result = schema_request.get_table_schema()
        if result["status"] == "error":
            logger.error(f"SQL DB GetSchema failed: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        logger.error(f"HTTP exception occurred: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("An unexpected error occurred.")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/powerbi/testconnection")
async def test_powerbi_connection(request: Request, connection_request: PowerBIRequest):
    verify_client_certificate(request)
    try:
        result = PowerBIRequest.test_connection(
            connection_request.tenantId,
            connection_request.token,
            connection_request.expires_on
        )
        if result["status"] == "error":
            logger.error(f"PBI Test Connection failed: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        logger.error(f"HTTP exception occurred: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("An unexpected error occurred.")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/fabric/testconnection")
async def test_fabric_connection(request: Request, connection_request: FabricRequest):
    verify_client_certificate(request)
    try:
        result = FabricRequest.test_connection(
            connection_request.account_name,
            connection_request.file_system_name,
            connection_request.directory_path,
            connection_request.token,
            connection_request.expires_on
        )
        if result["status"] == "error":
            logger.error(f"Fabric Test Connection failed: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        logger.error(f"HTTP exception occurred: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("An unexpected error occurred.")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/fabric/getdeltaschema")
async def get_fabric_schema(request: Request, schema_request: FabricDeltaSchemaRequest):
    verify_client_certificate(request)
    try:
        result = FabricDeltaSchemaRequest.get_table_schema(
            schema_request.account_name,
            schema_request.file_system_name,
            schema_request.directory_path,
            schema_request.token,
            schema_request.expires_on
        )
        if result["status"] == "error":
            logger.error(f"Fabric Delta GetSchema failed: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        logger.error(f"HTTP exception occurred: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("An unexpected error occurred.")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/fabric/getparquetschema")
async def get_fabric_schema(request: Request, schema_request: FabricParquetSchemaRequest):
    verify_client_certificate(request)
    try:
        result = FabricParquetSchemaRequest.get_table_schema(
            schema_request.account_name,
            schema_request.file_system_name,
            schema_request.directory_path,
            schema_request.token,
            schema_request.expires_on
        )
        if result["status"] == "error":
            logger.error(f"Fabric Parquet GetSchema failed: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        logger.error(f"HTTP exception occurred: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("An unexpected error occurred.")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/fabric/geticebergschema")
async def get_fabric_schema(request: Request, schema_request: FabricIcebergSchemaRequest):
    verify_client_certificate(request)
    try:
        result = FabricIcebergSchemaRequest.get_table_schema(
            schema_request.account_name,
            schema_request.file_system_name,
            schema_request.directory_path,
            schema_request.token,
            schema_request.expires_on
        )
        if result["status"] == "error":
            logger.error(f"Fabric Iceberg GetSchema failed: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        logger.error(f"HTTP exception occurred: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("An unexpected error occurred.")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/fabric/getformat")
async def get_fabric_format(request: Request, schema_request: FabricFormatDetector):
    verify_client_certificate(request)
    try:
        result = FabricFormatDetector.detect_format(
            schema_request.account_name,
            schema_request.file_system_name,
            schema_request.directory_path,
            schema_request.token,
            schema_request.expires_on
        )
        if result["status"] == "error":
            logger.error(f"Fabric GetFormat Detection failed: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        logger.error(f"HTTP exception occurred: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("An unexpected error occurred.")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.post("/fabric/getparquetpartitioncolumns")
async def get_fabric_getPartitionColumns(request: Request, schema_request: FabricFormatDetector):
    verify_client_certificate(request)
    try:
        result = FabricFormatDetector.detect_partitions(
            schema_request.account_name,
            schema_request.file_system_name,
            schema_request.directory_path,
            schema_request.token,
            schema_request.expires_on
        )
        if result["status"] == "error":
            logger.error(f"Fabric Parquet Partition Column Detection failed: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException as e:
        logger.error(f"HTTP exception occurred: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("An unexpected error occurred.")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

if __name__ == '__main__':
    app.run(debug=True)