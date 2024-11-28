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
from uvicorn.protocols.http.httptools_impl import HttpToolsProtocol

# Determine the environment
environment = os.getenv('ENVIRONMENT', 'DEV')

DQS_ENV_REGION = os.getenv('DQS_ENV_REGION', 'DEV')

print(f"Region PARAM : {DQS_ENV_REGION}")
client_ca_cert_file_path = "/app/certs"
os.makedirs(client_ca_cert_file_path, exist_ok=True)

# Fetch Key Vault names based on environment
if environment == "DEV":
    key_vault_name = os.getenv('DEV_KEYVAULT_NAME')
    cert_name = os.getenv('DEV_PFX_CERT_NAME')
    client_cert_names = os.getenv('DEV_CLIENT_PFX_CERT_NAMES', '').split(',')
elif environment == "PROD":
    key_vault_name = os.getenv('PROD_KEYVAULT_NAME')
    cert_name = os.getenv('PROD_PFX_CERT_NAME')
    client_cert_names = os.getenv('PROD_CLIENT_PFX_CERT_NAMES', '').split(',')
elif DQS_ENV_REGION == "uaenorth":
    key_vault_name = os.getenv('uaenorth_KEYVAULT_NAME')
    cert_name = os.getenv('uaenorth_PFX_CERT_NAME')
    client_cert_names = os.getenv('uaenorth_CLIENT_PFX_CERT_NAMES', '').split(',')
elif DQS_ENV_REGION == "eastus2euap":
    key_vault_name = os.getenv('eastus2euap_KEYVAULT_NAME')
    cert_name = os.getenv('eastus2euap_PFX_CERT_NAME')
    client_cert_names = os.getenv('eastus2euap_CLIENT_PFX_CERT_NAMES', '').split(',')
elif DQS_ENV_REGION == "australiaeast":
    key_vault_name = os.getenv('australiaeast_KEYVAULT_NAME')
    cert_name = os.getenv('australiaeast_PFX_CERT_NAME')
    client_cert_names = os.getenv('australiaeast_CLIENT_PFX_CERT_NAMES', '').split(',')
elif DQS_ENV_REGION == "brazilsouth":
    key_vault_name = os.getenv('brazilsouth_KEYVAULT_NAME')
    cert_name = os.getenv('brazilsouth_PFX_CERT_NAME')
    client_cert_names = os.getenv('brazilsouth_CLIENT_PFX_CERT_NAMES', '').split(',')
elif DQS_ENV_REGION == "canadaeast":
    key_vault_name = os.getenv('canadaeast_KEYVAULT_NAME')
    cert_name = os.getenv('canadaeast_PFX_CERT_NAME')
    client_cert_names = os.getenv('canadaeast_CLIENT_PFX_CERT_NAMES', '').split(',')
elif DQS_ENV_REGION == "canadacentral":
    key_vault_name = os.getenv('canadacentral_KEYVAULT_NAME')
    cert_name = os.getenv('canadacentral_PFX_CERT_NAME')
    client_cert_names = os.getenv('canadacentral_CLIENT_PFX_CERT_NAMES', '').split(',')
elif DQS_ENV_REGION == "centralindia":
    key_vault_name = os.getenv('centralindia_KEYVAULT_NAME')
    cert_name = os.getenv('centralindia_PFX_CERT_NAME')
    client_cert_names = os.getenv('centralindia_CLIENT_PFX_CERT_NAMES', '').split(',')
elif DQS_ENV_REGION == "centralus":
    key_vault_name = os.getenv('centralus_KEYVAULT_NAME')
    cert_name = os.getenv('centralus_PFX_CERT_NAME')
    client_cert_names = os.getenv('centralus_CLIENT_PFX_CERT_NAMES', '').split(',')
elif DQS_ENV_REGION == "germanywestcentral":
    key_vault_name = os.getenv('germanywestcentral_KEYVAULT_NAME')
    cert_name = os.getenv('germanywestcentral_PFX_CERT_NAME')
    client_cert_names = os.getenv('germanywestcentral_CLIENT_PFX_CERT_NAMES', '').split(',')
elif DQS_ENV_REGION == "eastus":
    key_vault_name = os.getenv('eastus_KEYVAULT_NAME')
    cert_name = os.getenv('eastus_PFX_CERT_NAME')
    client_cert_names = os.getenv('eastus_CLIENT_PFX_CERT_NAMES', '').split(',')
elif DQS_ENV_REGION == "eastus2":
    key_vault_name = os.getenv('eastus2_KEYVAULT_NAME')
    cert_name = os.getenv('eastus2_PFX_CERT_NAME')
    client_cert_names = os.getenv('eastus2_CLIENT_PFX_CERT_NAMES', '').split(',')
elif DQS_ENV_REGION == "francecentral":
    key_vault_name = os.getenv('francecentral_KEYVAULT_NAME')
    cert_name = os.getenv('francecentral_PFX_CERT_NAME')
    client_cert_names = os.getenv('francecentral_CLIENT_PFX_CERT_NAMES', '').split(',')
elif DQS_ENV_REGION == "japaneast":
    key_vault_name = os.getenv('japaneast_KEYVAULT_NAME')
    cert_name = os.getenv('japaneast_PFX_CERT_NAME')
    client_cert_names = os.getenv('japaneast_CLIENT_PFX_CERT_NAMES', '').split(',')
elif DQS_ENV_REGION == "koreacentral":
    key_vault_name = os.getenv('koreacentral_KEYVAULT_NAME')
    cert_name = os.getenv('koreacentral_PFX_CERT_NAME')
    client_cert_names = os.getenv('koreacentral_CLIENT_PFX_CERT_NAMES', '').split(',')
elif DQS_ENV_REGION == "southafricanorth":
    key_vault_name = os.getenv('southafricanorth_KEYVAULT_NAME')
    cert_name = os.getenv('southafricanorth_PFX_CERT_NAME')
    client_cert_names = os.getenv('southafricanorth_CLIENT_PFX_CERT_NAMES', '').split(',')
elif DQS_ENV_REGION == "swedencentral":
    key_vault_name = os.getenv('swedencentral_KEYVAULT_NAME')
    cert_name = os.getenv('swedencentral_PFX_CERT_NAME')
    client_cert_names = os.getenv('swedencentral_CLIENT_PFX_CERT_NAMES', '').split(',')
elif DQS_ENV_REGION == "southeastasia":
    key_vault_name = os.getenv('southeastasia_KEYVAULT_NAME')
    cert_name = os.getenv('southeastasia_PFX_CERT_NAME')
    client_cert_names = os.getenv('southeastasia_CLIENT_PFX_CERT_NAMES', '').split(',')
elif DQS_ENV_REGION == "southcentralus":
    key_vault_name = os.getenv('southcentralus_KEYVAULT_NAME')
    cert_name = os.getenv('southcentralus_PFX_CERT_NAME')
    client_cert_names = os.getenv('southcentralus_CLIENT_PFX_CERT_NAMES', '').split(',')
elif DQS_ENV_REGION == "switzerlandnorth":
    key_vault_name = os.getenv('switzerlandnorth_KEYVAULT_NAME')
    cert_name = os.getenv('switzerlandnorth_PFX_CERT_NAME')
    client_cert_names = os.getenv('switzerlandnorth_CLIENT_PFX_CERT_NAMES', '').split(',')
elif DQS_ENV_REGION == "uksouth":
    key_vault_name = os.getenv('uksouth_KEYVAULT_NAME')
    cert_name = os.getenv('uksouth_PFX_CERT_NAME')
    client_cert_names = os.getenv('uksouth_CLIENT_PFX_CERT_NAMES', '').split(',')
elif DQS_ENV_REGION == "westcentralus":
    key_vault_name = os.getenv('westcentralus_KEYVAULT_NAME')
    cert_name = os.getenv('westcentralus_PFX_CERT_NAME')
    client_cert_names = os.getenv('uksouth_CLIENT_PFX_CERT_NAMES', '').split(',')
elif DQS_ENV_REGION == "westus":
    key_vault_name = os.getenv('westus_KEYVAULT_NAME')
    cert_name = os.getenv('westus_PFX_CERT_NAME')
    client_cert_names = os.getenv('westus_CLIENT_PFX_CERT_NAMES', '').split(',')
elif DQS_ENV_REGION == "westus2":
    key_vault_name = os.getenv('westus2_KEYVAULT_NAME')
    cert_name = os.getenv('westus2_PFX_CERT_NAME')
    client_cert_names = os.getenv('westus2_CLIENT_PFX_CERT_NAMES', '').split(',')
elif DQS_ENV_REGION == "westeurope":
    key_vault_name = os.getenv('westeurope_KEYVAULT_NAME')
    cert_name = os.getenv('westeurope_PFX_CERT_NAME')
    client_cert_names = os.getenv('westeurope_CLIENT_PFX_CERT_NAMES', '').split(',')
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

## Client Certificate WhiteListing Begins
# Download client certificate (.pfx) from Key Vault for client authentication (mTLS)
with NamedTemporaryFile(delete=False, dir="/app/certs", suffix=".pem") as client_ca_cert_file:
    for client_cert_name in client_cert_names:
        # Fetch the client certificate from Key Vault
        client_certificate_operation = certificate_client.get_certificate(client_cert_name)
        client_pfx_secret = secret_client.get_secret(client_certificate_operation.name)
        # Decode the .pfx data
        client_pfx_data = base64.b64decode(client_pfx_secret.value)
        
        # Extract the certificates (including CA chain) from the PFX file
        _, _, client_ca_certs = pkcs12.load_key_and_certificates(client_pfx_data, password=None)

        # Write all additional client certificates (CA chain) into the CA cert file
        for ca_cert in client_ca_certs:
            client_ca_cert_file.write(ca_cert.public_bytes(Encoding.PEM))

    # Store the CA cert file path to be used later
    client_ca_cert_file_path = client_ca_cert_file.name

# Clean up temporary files after usage
def cleanup_files():
    try:
        Path(cert_file_path).unlink(missing_ok=True)
        Path(key_file_path).unlink(missing_ok=True)
        Path(client_ca_cert_file_path).unlink(missing_ok=True)
    except Exception as e:
        print(f"Error cleaning up files: {e}")

old_on_url = HttpToolsProtocol.on_url
def new_on_url(self,url):
    old_on_url(self, url)
    self.scope['transport'] = self.transport
HttpToolsProtocol.on_url = new_on_url

# Run Uvicorn with the SSL certificate, key, and client CA certificate for mutual TLS (mTLS)
try:
    if __name__ == "__main__":
        uvicorn.run(
            "src.main:app", 
            host="0.0.0.0", 
            port=443, 
            ssl_certfile=cert_file_path, 
            ssl_keyfile=key_file_path,
            ssl_ca_certs=client_ca_cert_file_path,  # Use client certificate's CA chain for client validation
            ssl_cert_reqs=ssl.CERT_REQUIRED  # Enforce client certificate authentication (mTLS)
            )
finally:
    cleanup_files()
END

#uvicorn src.main:app --host=0.0.0.0 --port=8000