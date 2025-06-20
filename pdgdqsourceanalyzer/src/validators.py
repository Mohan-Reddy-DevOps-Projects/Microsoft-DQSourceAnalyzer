import re
from urllib.parse import urlparse

class SourceValidators:
    @staticmethod
    def validate_account_url(value: str) -> str:
        value = value.strip().rstrip('/')
        if any(c in value for c in [';', '=', '?', ' ', '--']):
            raise ValueError("account_url must not contain semicolons, equals, question marks, spaces, or comment markers.")

        parsed_url = urlparse(value)
        if parsed_url.scheme.lower() != "https":
            raise ValueError("account_url must use HTTPS.")

        domain = parsed_url.netloc
        if len(domain) > 253:
            raise ValueError("account_url domain is too long (max 253 characters).")

        allowed_patterns = [
            r"^[a-z0-9]{3,24}\.[a-z0-9-]+\.(dfs|blob)\.storage\.azure\.net$",
            r"^[a-z0-9]{3,24}\.(blob|dfs)\.core\.windows\.net$",
        ]
        if not any(re.fullmatch(p, domain) for p in allowed_patterns):
            raise ValueError(f"Invalid account_url domain '{domain}'. Must match known Azure Storage patterns.")
        return value

    @staticmethod
    def not_empty(value):
        """Ensure no fields are empty."""
        if not value or value.strip() == "":
            raise ValueError('Field cannot be empty')
        return value.strip()
    
    @staticmethod
    def validate_fabric_account_name(value):
        """
        Only 'onelake' (all lowercase) is accepted as a valid account_name.
        """
        if isinstance(value, str):
            value = value.strip()
        else:
            raise ValueError("Invalid account_name. Value must be a string.")
        if value != "onelake":
            raise ValueError("Invalid account_name. Only lowercase 'onelake' is allowed.")
        return value
    @staticmethod
    def validate_server(value):
        # Disallow semicolons and connection string fragments
        if ';' in value or '=' in value or '/' in value:
            raise ValueError("Server Not authentic.")

        # Strict patterns for allowed services
        allowed_patterns = [
            r"^[a-z](?:[a-z0-9-]{1,61}[a-z0-9])?\.database\.windows\.net$",               # Azure SQL
            r"^[a-z][a-z0-9-]{1,61}[a-z0-9]\.sql\.azuresynapse\.net$",                    # Synapse Dedicated SQL pool
            r"^[a-z](?:[a-z0-9-]{1,61}[a-z0-9])?-ondemand\.sql\.azuresynapse\.net$",      # Synapse Serverless SQL
            r"^[a-z](?:[a-z0-9-]{1,61}[a-z0-9])\.datawarehouse\.fabric\.microsoft\.com$"  # Fabric
        ]


        if not any(re.fullmatch(p, value) for p in allowed_patterns):
            raise ValueError(
                f"Invalid server: '{value}'. Must be a well-formed Azure SQL, Synapse, or Fabric FQDN."
            )
        return value
    
    @staticmethod
    def validate_hostname(value):
        """Validate Databricks hostname format adb-<unique-id>.<shard>.azuredatabricks.net"""
        pattern = r"^adb-\d+\.\d+\.azuredatabricks\.net$"
        if not re.match(pattern, value):
            raise ValueError("Invalid Databricks hostname. Must follow 'adb-<unique-id>.<shard>.azuredatabricks.net' format.")
        return value
    
    @staticmethod
    def validate_project_id(value: str) -> str:
        if not re.fullmatch(r"[a-z][a-z0-9\-]{4,28}[a-z0-9]", value):
            raise ValueError("Invalid project_id. It must be 6-30 characters, start with a letter, contain only lowercase letters, digits, or hyphens, and cannot end with a hyphen.")
        return value

    @staticmethod
    def validate_dataset_or_table_id(value: str, field_name: str = "id") -> str:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,1023}", value):
            raise ValueError(f"Invalid {field_name}. It must start with a letter and only contain letters, numbers, or underscores, with a maximum length of 1024.")
        return value
    
    @staticmethod
    def validate_snowflake_account(value):
        """
        Validate Snowflake account FQDN.
        Accepts multi-label hostnames like:
        '<account>.<region>.snowflakecomputing.com' or '<account>.<region>.<cloud>.snowflakecomputing.com'.
        """
        # Disallow suspicious characters
        if any(c in value for c in [';', '=', ' ', '/', '--']):
            raise ValueError("Account not authentic. Contains illegal characters.")
        # Overall DNS name length (max 253 characters)
        if len(value) > 253:
            raise ValueError("Account FQDN too long (max 253 characters).")
        # Ensure it ends with the correct domain
        if not value.lower().endswith(".snowflakecomputing.com"):
            raise ValueError("Account must end with '.snowflakecomputing.com'.")
        # Split and validate all DNS labels
        labels = value.split('.')
        if len(labels) < 3:
            raise ValueError("Incomplete account domain. Expected at least 3 parts before '.snowflakecomputing.com'.")

        for label in labels:
            if not re.fullmatch(r"[a-zA-Z0-9-]{1,63}", label):
                raise ValueError(f"Invalid label '{label}'. Must be 1-63 alphanumeric or hyphen characters.")
            if label.startswith('-') or label.endswith('-'):
                raise ValueError(f"Label '{label}' cannot start or end with a hyphen.")
        return value
    
    @staticmethod
    def validate_expires_on(value):
        if not isinstance(value, int):
            raise ValueError("Value must be an integer")
        if value <= 0:
            raise ValueError("Value must be a positive integer")
        if value > 2_147_483_647:
            raise ValueError("Value exceeds 32-bit signed integer max limit")
        return value
