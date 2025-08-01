# 🚀 S3 Upload Guide for Challenge Videos

## **Overview**
This guide explains how to upload videos to S3 for challenge submissions using our secure, authenticated flow.

## **📋 Current Implementation**

### **Option 1: Unified Submission (RECOMMENDED)**
**Single API call** that handles everything:
```bash
POST /api/challenges/{challenge_id}/submit-unified
```

**Request Body:**
```json
{
    "video_file": "base64_encoded_video_data",
    "metadata": {
        "caption": "My challenge attempt!",
        "tags": ["freestyle", "challenge"],
        "location": "Mumbai, India",
        "isPublic": true,
        "sharedToFeed": true,
        "highlightText": "Check out my moves!"
    }
}
```

**What happens:**
1. ✅ Video is processed and uploaded to S3
2. ✅ Session is created automatically
3. ✅ Submission is created with unified structure
4. ✅ AI analysis is triggered automatically
5. ✅ All metadata is saved

## **🔧 S3 Upload Flow (For Frontend Implementation)**

### **Step 1: Get Presigned URL**
```bash
POST /api/s3/upload/challenge-video
Authorization: Bearer YOUR_TOKEN

{
    "challenge_id": "68885e917dcfd112158b2a10",
    "file_extension": "mp4",
    "content_type": "video/mp4",
    "file_size_mb": 25.5
}
```

**Response:**
```json
{
    "upload_url": "https://bucket.s3.amazonaws.com/...",
    "file_key": "challenges/user123/challenge456/20250128_153000_abc12345.mp4",
    "content_type": "video/mp4",
    "expires_in": 7200,
    "file_url": "https://bucket.s3.amazonaws.com/challenges/user123/challenge456/20250128_153000_abc12345.mp4"
}
```

### **Step 2: Upload Video to S3**
```bash
curl -X PUT \
  -H "Content-Type: video/mp4" \
  --upload-file your_video.mp4 \
  "https://bucket.s3.amazonaws.com/..."
```

### **Step 3: Submit Challenge with S3 Details**
```bash
POST /api/challenges/{challenge_id}/submit-unified
Authorization: Bearer YOUR_TOKEN

{
    "video_file": "s3://bucket/challenges/user123/challenge456/20250128_153000_abc12345.mp4",
    "metadata": {
        "caption": "My challenge attempt!",
        "tags": ["freestyle", "challenge"],
        "location": "Mumbai, India",
        "isPublic": true,
        "sharedToFeed": true
    }
}
```

## **🎯 Frontend Implementation Example**

### **React/JavaScript Example:**
```javascript
// Step 1: Get presigned URL
const getUploadUrl = async (challengeId, file) => {
    const response = await fetch('/api/s3/upload/challenge-video', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            challenge_id: challengeId,
            file_extension: 'mp4',
            content_type: 'video/mp4',
            file_size_mb: file.size / (1024 * 1024)
        })
    });
    
    return response.json();
};

// Step 2: Upload to S3
const uploadToS3 = async (uploadUrl, file) => {
    await fetch(uploadUrl, {
        method: 'PUT',
        body: file,
        headers: {
            'Content-Type': 'video/mp4'
        }
    });
};

// Step 3: Submit challenge
const submitChallenge = async (challengeId, s3FileKey, metadata) => {
    const response = await fetch(`/api/challenges/${challengeId}/submit-unified`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            video_file: s3FileKey,
            metadata: metadata
        })
    });
    
    return response.json();
};

// Complete flow
const uploadChallengeVideo = async (challengeId, videoFile, metadata) => {
    try {
        // 1. Get presigned URL
        const { upload_url, file_key } = await getUploadUrl(challengeId, videoFile);
        
        // 2. Upload to S3
        await uploadToS3(upload_url, videoFile);
        
        // 3. Submit challenge
        const submission = await submitChallenge(challengeId, file_key, metadata);
        
        console.log('✅ Challenge submitted successfully:', submission);
        return submission;
        
    } catch (error) {
        console.error('❌ Error uploading challenge video:', error);
        throw error;
    }
};
```

## **🔒 Security Features**

### **✅ Authentication Required**
- All endpoints require valid JWT token
- User can only upload to their own challenges

### **✅ Presigned URLs**
- Temporary URLs (2 hours expiry)
- Direct upload to S3 (no server bandwidth)
- Secure file key generation

### **✅ File Validation**
- File size limits
- File type validation
- Challenge existence validation

### **✅ Duplicate Prevention**
- One submission per user per challenge
- Automatic duplicate detection

## **📊 Response Structure**

### **Unified Submission Response:**
```json
{
    "id": "submission_id",
    "challengeId": "challenge_id",
    "userId": "user_id",
    "video": {
        "url": "https://bucket.s3.amazonaws.com/...",
        "file_key": "challenges/user123/challenge456/...",
        "duration": 60,
        "size_mb": 25.5
    },
    "analysis": {
        "status": "pending",
        "score": null,
        "breakdown": null,
        "feedback": null,
        "pose_data_url": null,
        "confidence": null
    },
    "metadata": {
        "caption": "My challenge attempt!",
        "tags": ["freestyle", "challenge"],
        "location": "Mumbai, India",
        "isPublic": true,
        "sharedToFeed": true,
        "highlightText": "Check out my moves!"
    },
    "userProfile": {
        "displayName": "John Doe",
        "avatarUrl": "https://...",
        "level": 5
    },
    "timestamps": {
        "submittedAt": "2025-01-28T15:30:00Z",
        "processedAt": null,
        "analyzedAt": null
    },
    "likes": [],
    "comments": [],
    "shares": 0
}
```

## **🔄 Status Tracking**

### **Analysis Status:**
- `pending` - Analysis started
- `processing` - AI analyzing video
- `completed` - Analysis finished
- `failed` - Analysis failed

### **Check Analysis Status:**
```bash
GET /api/ai/analysis-status/{submission_id}
```

## **🚨 Error Handling**

### **Common Errors:**
- `400` - Already submitted to this challenge
- `404` - Challenge not found
- `401` - Unauthorized
- `413` - File too large
- `415` - Unsupported file type

### **Retry Logic:**
- S3 upload failures can be retried
- Analysis failures don't affect submission
- Network timeouts should be handled

## **📱 Mobile App Integration**

### **React Native Example:**
```javascript
import { launchCamera, launchImageLibrary } from 'react-native-image-picker';

const recordChallengeVideo = async (challengeId) => {
    try {
        // 1. Record video
        const result = await launchCamera({
            mediaType: 'video',
            quality: 0.8,
            maxDuration: 60
        });
        
        if (result.assets && result.assets[0]) {
            const videoFile = result.assets[0];
            
            // 2. Upload and submit
            const submission = await uploadChallengeVideo(
                challengeId, 
                videoFile, 
                {
                    caption: "My challenge attempt!",
                    tags: ["freestyle"],
                    location: "Mumbai",
                    isPublic: true,
                    sharedToFeed: true
                }
            );
            
            console.log('✅ Challenge submitted:', submission);
        }
        
    } catch (error) {
        console.error('❌ Error recording challenge video:', error);
    }
};
```

## **🎯 Best Practices**

### **✅ Do:**
- Compress videos before upload
- Show upload progress
- Handle network errors gracefully
- Validate file size before upload
- Show analysis status to user

### **❌ Don't:**
- Upload without authentication
- Skip file validation
- Ignore upload errors
- Block UI during upload
- Forget to handle timeouts

## **🔧 Configuration**

### **Environment Variables:**
```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=ap-south-1
S3_BUCKET_NAME=your_bucket_name
```

### **File Limits:**
- Max file size: 100MB
- Supported formats: MP4, MOV, AVI
- Max duration: 5 minutes
- Presigned URL expiry: 2 hours

---

**🎉 Your challenge video upload system is ready!** 