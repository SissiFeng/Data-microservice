import boto3
import os
from botocore.exceptions import ClientError
from app.core.config import settings

def get_s3_client():
    """
    Get an S3 client
    """
    return boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION
    )

def upload_file(file_path, s3_key):
    """
    Upload a file to S3
    
    Parameters:
    -----------
    file_path : str
        Path to the local file
    s3_key : str
        S3 object key
    
    Returns:
    --------
    bool
        True if file was uploaded successfully, else False
    """
    s3_client = get_s3_client()
    try:
        s3_client.upload_file(file_path, settings.S3_BUCKET_NAME, s3_key)
        return True
    except ClientError as e:
        print(f"Error uploading file to S3: {str(e)}")
        return False

def download_file(s3_key, local_path):
    """
    Download a file from S3
    
    Parameters:
    -----------
    s3_key : str
        S3 object key
    local_path : str
        Path to save the file locally
    
    Returns:
    --------
    bool
        True if file was downloaded successfully, else False
    """
    s3_client = get_s3_client()
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        s3_client.download_file(settings.S3_BUCKET_NAME, s3_key, local_path)
        return True
    except ClientError as e:
        print(f"Error downloading file from S3: {str(e)}")
        return False

def delete_file(s3_key):
    """
    Delete a file from S3
    
    Parameters:
    -----------
    s3_key : str
        S3 object key
    
    Returns:
    --------
    bool
        True if file was deleted successfully, else False
    """
    s3_client = get_s3_client()
    try:
        s3_client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=s3_key)
        return True
    except ClientError as e:
        print(f"Error deleting file from S3: {str(e)}")
        return False

def list_files(prefix=""):
    """
    List files in S3 bucket
    
    Parameters:
    -----------
    prefix : str
        Prefix to filter objects
    
    Returns:
    --------
    list
        List of object keys
    """
    s3_client = get_s3_client()
    try:
        response = s3_client.list_objects_v2(
            Bucket=settings.S3_BUCKET_NAME,
            Prefix=prefix
        )
        
        if 'Contents' in response:
            return [obj['Key'] for obj in response['Contents']]
        return []
    except ClientError as e:
        print(f"Error listing files in S3: {str(e)}")
        return []
