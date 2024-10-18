#!/bin/bash

# Load environment variables from .env
set -a
source .env
set -e

ENVIRONMENT=${ENVIRONMENT:-DEV}  # Default to DEV if not provided

python3 << END
import os
import base64
import ssl
import uvicorn
from azure.identity import DefaultAzureCredential,ClientSecretCredential
from azure.keyvault.certificates import CertificateClient
from azure.keyvault.secrets import SecretClient
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
from tempfile import NamedTemporaryFile
from pathlib import Path

# Determine the environment
environment = os.getenv('ENVIRONMENT', 'DEV')

# Fetch Key Vault names based on environment
if environment == "DEV":
    key_vault_name = os.getenv('DEV_KEYVAULT_NAME')
    cert_name = os.getenv('DEV_PFX_CERT_NAME')
elif environment == "PROD":
    key_vault_name = os.getenv('PROD_KEYVAULT_NAME')
    cert_name = os.getenv('PROD_PFX_CERT_NAME')
else:
    raise ValueError("Invalid environment specified.")

key_vault_url = f"https://{key_vault_name}.vault.azure.net/"

# Use DefaultAzureCredential for Managed Identity (MSI) authentication
credential = DefaultAzureCredential()

certificate_client = CertificateClient(vault_url=key_vault_url, credential=credential)
certificate_operation = certificate_client.get_certificate(cert_name)

# Download the .pfx file by accessing the certificate's secret
# To retrieve the .pfx file, we use the SecretClient, as certificates are stored as secrets.
secret_client = SecretClient(vault_url=key_vault_url, credential=credential)
pfx_secret = secret_client.get_secret(certificate_operation.name)

# The .pfx data is base64-encoded, so we decode it
pfx_data = base64.b64decode(pfx_secret.value)

# Parse the PFX file to extract the private key and certificate
private_key, cert, additional_certs = pkcs12.load_key_and_certificates(pfx_data, password=None)

# Create temporary certificate and key files to be used by Uvicorn
with NamedTemporaryFile(delete=False) as cert_file, NamedTemporaryFile(delete=False) as key_file:
    cert_file.write(cert.public_bytes(Encoding.PEM))
    key_file.write(private_key.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=NoEncryption()
    ))
    cert_file_path = cert_file.name
    key_file_path = key_file.name

# Clean up temporary files after usage
def cleanup_files():
    try:
        Path(cert_file_path).unlink(missing_ok=True)
        Path(key_file_path).unlink(missing_ok=True)
    except Exception as e:
        print(f"Error cleaning up files: {e}")

# Run Uvicorn with the SSL certificate and key files
try:
    if __name__ == "__main__":
        uvicorn.run("src.main:app", host="0.0.0.0", port=443, ssl_certfile=cert_file_path, ssl_keyfile=key_file_path)
finally:
    cleanup_files()

END

#uvicorn src.main:app --host=0.0.0.0 --port=8000