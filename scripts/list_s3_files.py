#!/usr/bin/env python3
"""
Script to list all files in S3 bucket
Shows all files that exist in S3, including orphaned files
"""

import os
import sys
import boto3
from botocore.exceptions import ClientError
from datetime import datetime

def list_s3_files():
    """List all files in S3 bucket"""
    try:
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        
        bucket_name = os.getenv('S3_BUCKET_NAME', 'idanceshreyansh')
        
        print(f"🔍 Listing files in S3 bucket: {bucket_name}")
        print(f"⏰ Timestamp: {datetime.now()}")
        print()
        
        # List all objects in the bucket
        paginator = s3_client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=bucket_name)
        
        all_files = []
        total_size = 0
        
        for page in page_iterator:
            if 'Contents' in page:
                for obj in page['Contents']:
                    all_files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified']
                    })
                    total_size += obj['Size']
        
        if not all_files:
            print("✅ S3 bucket is empty!")
            return
        
        print(f"📊 Found {len(all_files)} files in S3 bucket")
        print(f"💾 Total size: {total_size / (1024*1024):.2f} MB")
        print()
        
        # Group files by directory
        file_groups = {}
        for file_info in all_files:
            key = file_info['key']
            if '/' in key:
                directory = key.split('/')[0]
            else:
                directory = 'root'
            
            if directory not in file_groups:
                file_groups[directory] = []
            file_groups[directory].append(file_info)
        
        # Print files grouped by directory
        for directory, files in sorted(file_groups.items()):
            print(f"📁 {directory}/ ({len(files)} files)")
            for file_info in files[:10]:  # Show first 10 files per directory
                size_mb = file_info['size'] / (1024*1024)
                print(f"  - {file_info['key']} ({size_mb:.2f} MB)")
            
            if len(files) > 10:
                print(f"  ... and {len(files) - 10} more files")
            print()
        
        # Show summary by file type
        print("📈 File type summary:")
        file_types = {}
        for file_info in all_files:
            key = file_info['key']
            if '.' in key:
                ext = key.split('.')[-1].lower()
            else:
                ext = 'no_extension'
            
            if ext not in file_types:
                file_types[ext] = {'count': 0, 'size': 0}
            file_types[ext]['count'] += 1
            file_types[ext]['size'] += file_info['size']
        
        for ext, info in sorted(file_types.items()):
            size_mb = info['size'] / (1024*1024)
            print(f"  - .{ext}: {info['count']} files ({size_mb:.2f} MB)")
        
    except ClientError as e:
        print(f"❌ S3 Error: {str(e)}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    list_s3_files() 