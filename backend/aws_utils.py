import boto3
import os
from botocore.exceptions import ClientError
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, S3_BUCKET_NAME

def get_s3_client():
    """Create and return S3 client"""
    return boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )

def upload_string_to_s3(content, s3_key, content_type='text/plain'):
    """Upload string or bytes content directly to S3"""
    try:
        s3_client = get_s3_client()
        if isinstance(content, str):
            body = content.encode('utf-8')
        elif isinstance(content, bytes):
            body = content
        else:
            body = str(content).encode('utf-8')
        
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=body,
            ContentType=content_type
        )
        s3_url = f"s3://{S3_BUCKET_NAME}/{s3_key}"
        return True, s3_url
    except ClientError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)

def get_presigned_url(s3_key, expiration=3600):
    """Generate a presigned URL for downloading file from S3"""
    try:
        s3_client = get_s3_client()
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=expiration
        )
        return True, url
    except ClientError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)

def list_files_in_s3(prefix=''):
    """List files in S3 bucket with given prefix"""
    try:
        s3_client = get_s3_client()
        files = []
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=S3_BUCKET_NAME, Prefix=prefix)
        
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat()
                    })
        
        files.sort(key=lambda x: x['last_modified'], reverse=True)
        return True, files
    except ClientError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)

