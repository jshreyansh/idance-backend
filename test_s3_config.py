#!/usr/bin/env python3
"""
Test S3 Configuration Script
This script tests the S3 configuration and checks CORS headers
"""

import os
import boto3
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_s3_configuration():
    """Test S3 configuration and CORS headers"""
    print("🔧 Testing S3 Configuration...")
    
    # Get environment variables
    bucket_name = os.getenv('S3_BUCKET_NAME')
    bucket_url = os.getenv('S3_BUCKET_URL')
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_region = os.getenv('AWS_REGION')
    
    print(f"📊 Configuration:")
    print(f"  - Bucket Name: {bucket_name}")
    print(f"  - Bucket URL: {bucket_url}")
    print(f"  - AWS Region: {aws_region}")
    print(f"  - AWS Access Key: {'✅ Set' if aws_access_key else '❌ Not set'}")
    print(f"  - AWS Secret Key: {'✅ Set' if aws_secret_key else '❌ Not set'}")
    
    if not all([bucket_name, bucket_url, aws_access_key, aws_secret_key, aws_region]):
        print("❌ Missing required environment variables!")
        return False
    
    try:
        # Test S3 client connection
        print("\n🔗 Testing S3 Client Connection...")
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        
        # Test bucket access
        response = s3_client.head_bucket(Bucket=bucket_name)
        print(f"✅ S3 bucket access successful: {bucket_name}")
        
        # Test CORS configuration
        print("\n🌐 Testing CORS Configuration...")
        try:
            cors_response = s3_client.get_bucket_cors(Bucket=bucket_name)
            cors_rules = cors_response.get('CORSRules', [])
            
            if cors_rules:
                print(f"✅ CORS configuration found with {len(cors_rules)} rules")
                for i, rule in enumerate(cors_rules):
                    print(f"  Rule {i+1}:")
                    print(f"    Allowed Origins: {rule.get('AllowedOrigins', [])}")
                    print(f"    Allowed Methods: {rule.get('AllowedMethods', [])}")
                    print(f"    Allowed Headers: {rule.get('AllowedHeaders', [])}")
                    print(f"    Expose Headers: {rule.get('ExposeHeaders', [])}")
            else:
                print("❌ No CORS rules found!")
                return False
                
        except Exception as e:
            print(f"❌ Error getting CORS configuration: {e}")
            return False
        
        # Test bucket policy
        print("\n🔒 Testing Bucket Policy...")
        try:
            policy_response = s3_client.get_bucket_policy(Bucket=bucket_name)
            print("✅ Bucket policy found")
        except Exception as e:
            print(f"❌ Error getting bucket policy: {e}")
            return False
        
        # Test a simple file upload and download
        print("\n📤 Testing File Upload/Download...")
        test_key = "test-mobile-compatibility.txt"
        test_content = "This is a test file for mobile compatibility"
        
        # Upload test file
        s3_client.put_object(
            Bucket=bucket_name,
            Key=test_key,
            Body=test_content,
            ContentType='text/plain'
        )
        print(f"✅ Test file uploaded: {test_key}")
        
        # Generate presigned URL
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': test_key},
            ExpiresIn=3600
        )
        print(f"✅ Presigned URL generated: {presigned_url[:50]}...")
        
        # Test direct access
        direct_url = f"{bucket_url}/{test_key}"
        print(f"✅ Direct URL: {direct_url}")
        
        # Test CORS headers with a request
        print("\n🌐 Testing CORS Headers...")
        headers = {
            'Origin': 'https://dansync.xyz',
            'Referer': 'https://dansync.xyz/'
        }
        
        # Use GET request instead of HEAD to see CORS headers
        response = requests.get(direct_url, headers=headers)
        print(f"Response Status: {response.status_code}")
        
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
            'Access-Control-Max-Age': response.headers.get('Access-Control-Max-Age')
        }
        
        print("CORS Headers in Response:")
        for header, value in cors_headers.items():
            status = "✅" if value else "❌"
            print(f"  {status} {header}: {value}")
        
        # Also test with OPTIONS request (preflight)
        print("\n🛫 Testing OPTIONS Request (Preflight)...")
        options_response = requests.options(direct_url, headers=headers)
        print(f"OPTIONS Response Status: {options_response.status_code}")
        
        options_cors_headers = {
            'Access-Control-Allow-Origin': options_response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': options_response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': options_response.headers.get('Access-Control-Allow-Headers'),
            'Access-Control-Max-Age': options_response.headers.get('Access-Control-Max-Age')
        }
        
        print("OPTIONS CORS Headers:")
        for header, value in options_cors_headers.items():
            status = "✅" if value else "❌"
            print(f"  {status} {header}: {value}")
        
        # Clean up test file
        s3_client.delete_object(Bucket=bucket_name, Key=test_key)
        print(f"✅ Test file cleaned up: {test_key}")
        
        print("\n🎉 S3 Configuration Test Completed Successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing S3 configuration: {e}")
        return False

if __name__ == "__main__":
    success = test_s3_configuration()
    if success:
        print("\n✅ Your S3 configuration is ready for mobile video uploads!")
        print("📱 All new videos should work on mobile browsers.")
    else:
        print("\n❌ S3 configuration needs to be fixed before testing mobile uploads.") 