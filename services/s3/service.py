import boto3
import os
from botocore.exceptions import ClientError
from fastapi import HTTPException
from datetime import datetime, timedelta
import uuid
from typing import Optional

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION'),
            config=boto3.session.Config(
                connect_timeout=60,
                read_timeout=300,
                retries={'max_attempts': 3}
            )
        )
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
        self.bucket_url = os.getenv('S3_BUCKET_URL')
        
    def generate_presigned_upload_url(self, file_key: str, content_type: str = 'video/mp4', expires_in: int = 7200) -> dict:
        """
        Generate a presigned URL for uploading a video file to S3
        """
        try:
            # Generate presigned URL for PUT operation
            presigned_url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_key,
                    'ContentType': content_type
                },
                ExpiresIn=expires_in
            )
            
            return {
                'upload_url': presigned_url,
                'file_key': file_key,
                'content_type': content_type,
                'expires_in': expires_in
            }
        except ClientError as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate presigned URL: {str(e)}")
    
    def generate_presigned_download_url(self, file_key: str, expires_in: int = 3600) -> str:
        """
        Generate a presigned URL for downloading a video file from S3
        """
        try:
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_key
                },
                ExpiresIn=expires_in
            )
            return presigned_url
        except ClientError as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate download URL: {str(e)}")
    
    def delete_file(self, file_key: str) -> bool:
        """
        Delete a file from S3
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            return True
        except ClientError as e:
            print(f"Failed to delete file {file_key}: {str(e)}")
            return False
    
    def file_exists(self, file_key: str) -> bool:
        """
        Check if a file exists in S3
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=file_key)
            return True
        except ClientError:
            return False
    
    def get_file_url(self, file_key: str) -> str:
        """
        Get the public URL for a file (if bucket is public) or generate a presigned URL
        """
        if self.bucket_url:
            return f"{self.bucket_url.rstrip('/')}/{file_key}"
        else:
            return self.generate_presigned_download_url(file_key)

# Global S3 service instance
s3_service = S3Service()

def generate_session_video_key(user_id: str, session_id: str, file_extension: str = 'mp4') -> str:
    """
    Generate a unique S3 key for session videos
    Format: sessions/{user_id}/{session_id}/{timestamp}.{extension}
    """
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    return f"sessions/{user_id}/{session_id}/{timestamp}_{unique_id}.{file_extension}"

def generate_thumbnail_key(user_id: str, session_id: str, file_extension: str = 'jpg') -> str:
    """
    Generate a unique S3 key for video thumbnails
    """
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    return f"thumbnails/{user_id}/{session_id}/{timestamp}_{unique_id}.{file_extension}" 