"""Secrets helper using AWS SSM Parameter Store with role chaining."""
import os
import json
import boto3

_credentials = None

def get_credentials(force_refresh=False):
    """Assume the exec role to get privileged credentials."""
    global _credentials
    if _credentials is not None and not force_refresh:
        return _credentials
    
    sts = boto3.client("sts")
    res = sts.assume_role(
        RoleArn=os.environ["SamsaraFunctionExecRoleArn"],
        RoleSessionName=os.environ.get("SamsaraFunctionName", "function"),
    )
    _credentials = {
        "aws_access_key_id": res["Credentials"]["AccessKeyId"],
        "aws_secret_access_key": res["Credentials"]["SecretAccessKey"],
        "aws_session_token": res["Credentials"]["SessionToken"],
    }
    return _credentials

def get_secrets():
    """Fetch secrets from SSM Parameter Store."""
    secrets_path = os.environ.get("SamsaraFunctionSecretsPath")
    if not secrets_path:
        return {}
    
    creds = get_credentials()
    ssm = boto3.client("ssm", **creds)
    
    try:
        response = ssm.get_parameter(Name=secrets_path, WithDecryption=True)
        value = response["Parameter"]["Value"]
        return json.loads(value)
    except Exception as e:
        print(f"Error fetching secrets: {e}")
        return {}
