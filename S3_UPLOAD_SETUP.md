# S3 Upload System Setup and Usage

## Overview
The iDance backend now includes a comprehensive S3 upload system for handling session videos and thumbnails. The system uses presigned URLs for secure, direct uploads to S3 without passing files through the backend server.

## Architecture

### Components
1. **S3Service** (`services/s3/service.py`): Core S3 operations
2. **S3 Router** (`services/s3/router.py`): API endpoints for upload URLs
3. **Session Integration**: Updated session models and completion flow
4. **Security**: User-based access control and file key validation

### File Structure
```
sessions/{user_id}/{session_id}/{timestamp}_{unique_id}.mp4
thumbnails/{user_id}/{session_id}/{timestamp}_{unique_id}.jpg
```

## Setup Instructions

### 1. Environment Variables
Add these to your `.env` file:
```bash
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-s3-bucket-name
S3_BUCKET_URL=https://your-s3-bucket-name.s3.us-east-1.amazonaws.com
```

### 2. S3 Bucket Configuration
1. Create an S3 bucket in your AWS account
2. Configure CORS for the bucket:
```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
        "AllowedOrigins": ["*"],
        "ExposeHeaders": []
    }
]
```
3. Set appropriate bucket permissions (public or private based on your needs)

### 3. Install Dependencies
```bash
pip install boto3==1.34.0
```

## API Endpoints

### 1. Get Video Upload URL
**POST** `/api/s3/upload/video`

**Request Body:**
```json
{
    "session_id": "session_id_here",
    "file_extension": "mp4",
    "content_type": "video/mp4",
    "file_size_mb": 25.5
}
```

**Response:**
```json
{
    "upload_url": "https://presigned-s3-upload-url",
    "file_key": "sessions/user123/session456/20241201_143022_abc123.mp4",
    "content_type": "video/mp4",
    "expires_in": 3600,
    "file_url": "https://your-bucket.s3.region.amazonaws.com/sessions/user123/session456/20241201_143022_abc123.mp4"
}
```

### 2. Get Thumbnail Upload URL
**POST** `/api/s3/upload/thumbnail`

**Request Body:**
```json
{
    "session_id": "session_id_here",
    "file_extension": "jpg",
    "content_type": "image/jpeg"
}
```

### 3. Delete File
**DELETE** `/api/s3/files/{file_key}`

### 4. Get File Download URL
**GET** `/api/s3/files/{file_key}/url`

## Usage Flow

### Complete Video Upload Process

1. **Start Session**
   ```bash
   POST /api/sessions/start
   ```

2. **Get Upload URL**
   ```bash
   POST /api/s3/upload/video
   {
       "session_id": "session_id_from_step_1"
   }
   ```

3. **Upload Video to S3**
   ```bash
   # Use the upload_url from step 2 to upload directly to S3
   PUT {upload_url}
   Content-Type: video/mp4
   Body: video_file_binary_data
   ```

4. **Complete Session with Video URL**
   ```bash
   POST /api/sessions/complete
   {
       "sessionId": "session_id",
       "endTime": "2024-12-01T14:30:00Z",
       "durationMinutes": 30,
       "caloriesBurned": 150,
       "videoURL": "https://your-bucket.s3.region.amazonaws.com/sessions/user123/session456/20241201_143022_abc123.mp4",
       "videoFileKey": "sessions/user123/session456/20241201_143022_abc123.mp4"
   }
   ```

## Frontend Integration Example

### JavaScript/TypeScript Example
```javascript
async function uploadSessionVideo(sessionId, videoFile) {
    // 1. Get upload URL
    const uploadResponse = await fetch('/api/s3/upload/video', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            session_id: sessionId,
            file_extension: 'mp4',
            content_type: 'video/mp4'
        })
    });
    
    const { upload_url, file_key, file_url } = await uploadResponse.json();
    
    // 2. Upload to S3
    await fetch(upload_url, {
        method: 'PUT',
        headers: {
            'Content-Type': 'video/mp4'
        },
        body: videoFile
    });
    
    // 3. Complete session with video URL
    await fetch('/api/sessions/complete', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            sessionId: sessionId,
            endTime: new Date().toISOString(),
            durationMinutes: 30,
            caloriesBurned: 150,
            videoURL: file_url,
            videoFileKey: file_key
        })
    });
}
```

## Security Features

1. **User Authentication**: All upload endpoints require valid JWT tokens
2. **Session Ownership**: Users can only upload videos for their own sessions
3. **File Key Validation**: File keys are validated to ensure they belong to the user
4. **Presigned URLs**: Temporary, secure URLs with expiration times
5. **Unique File Names**: Timestamp and UUID-based naming prevents conflicts

## Error Handling

The system handles various error scenarios:
- Invalid session ownership
- S3 upload failures
- Expired presigned URLs
- File size limits (configured in S3 bucket)
- Network timeouts

## Monitoring and Logging

Consider adding:
- CloudWatch logs for S3 operations
- Metrics for upload success/failure rates
- File size and type validation
- Upload progress tracking

## Cost Optimization

1. **Lifecycle Policies**: Set up S3 lifecycle policies to move old videos to cheaper storage
2. **CDN Integration**: Use CloudFront for video delivery
3. **Compression**: Implement video compression before upload
4. **Cleanup**: Regular cleanup of orphaned files

## Testing

Test the system with:
1. Small video files (< 10MB)
2. Large video files (> 100MB)
3. Invalid file types
4. Expired presigned URLs
5. Network interruptions during upload 