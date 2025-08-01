# 🧪 Challenge System Testing Guide

## **📋 Quick Start**

### **1. Start Server**
```bash
cd /Users/shreyansh/idance-backend
source venv/bin/activate
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### **2. Test Challenge Flow**
Follow the step-by-step guide below.

## **🔐 Step 1: Login & Get Token**

### **POST /api/auth/login**
```http
POST http://localhost:8000/api/auth/login
Content-Type: application/json

{
    "email": "jshreyansh37@gmail.com",
    "password": "17Je318$sj"
}
```

**Save the `token` from response for all subsequent requests.**

## **🏆 Step 2: Create Challenge**

### **POST /api/challenges**
```http
POST http://localhost:8000/api/challenges
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
    "title": "Morning Dance Challenge",
    "description": "Start your day with energy!",
    "type": "freestyle",
    "difficulty": "beginner",
    "category": "morning",
    "tags": ["morning", "energy", "freestyle"],
    "startTime": "2025-01-28T00:00:00Z",
    "endTime": "2025-01-29T23:59:59Z",
    "demoVideoURL": "https://example.com/demo.mp4",
    "scoringCriteria": {
        "balance": 25,
        "rhythm": 25,
        "smoothness": 25,
        "creativity": 25
    },
    "isActive": true
}
```

**Save the `challenge_id` from response.**

## **📤 Step 3: Submit Challenge (Unified Flow)**

### **POST /api/challenges/{challenge_id}/submit-unified**
```http
POST http://localhost:8000/api/challenges/YOUR_CHALLENGE_ID/submit-unified
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
    "video_file": "base64_encoded_video_data_here",
    "metadata": {
        "caption": "My morning dance challenge!",
        "tags": ["freestyle", "morning", "energy"],
        "location": "Mumbai, India",
        "isPublic": true,
        "sharedToFeed": true,
        "highlightText": "Check out my moves!"
    }
}
```

**Save the `submission_id` from response.**

## **🔍 Step 4: Check Analysis Status**

### **GET /api/ai/analysis-status/{submission_id}**
```http
GET http://localhost:8000/api/ai/analysis-status/YOUR_SUBMISSION_ID
Authorization: Bearer YOUR_TOKEN
```

## **📊 Step 5: View Results**

### **GET /api/challenges/{challenge_id}/submissions**
```http
GET http://localhost:8000/api/challenges/YOUR_CHALLENGE_ID/submissions?page=1&limit=10
Authorization: Bearer YOUR_TOKEN
```

### **GET /api/submissions/{submission_id}**
```http
GET http://localhost:8000/api/submissions/YOUR_SUBMISSION_ID
Authorization: Bearer YOUR_TOKEN
```

## **🔧 S3 Upload Flow (For Large Files)**

### **Step 1: Get Presigned URL**
```http
POST http://localhost:8000/api/s3/upload/challenge-video
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
    "challenge_id": "YOUR_CHALLENGE_ID",
    "file_extension": "mp4",
    "content_type": "video/mp4",
    "file_size_mb": 25.5
}
```

### **Step 2: Upload to S3**
```bash
curl -X PUT \
  -H "Content-Type: video/mp4" \
  --upload-file your_video.mp4 \
  "UPLOAD_URL_FROM_STEP_1"
```

### **Step 3: Submit with S3 File Key**
```http
POST http://localhost:8000/api/challenges/YOUR_CHALLENGE_ID/submit-unified
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
    "video_file": "FILE_KEY_FROM_STEP_1",
    "metadata": {
        "caption": "My S3 uploaded challenge!",
        "tags": ["freestyle", "s3"],
        "location": "Mumbai, India",
        "isPublic": true,
        "sharedToFeed": true
    }
}
```

## **📝 Additional Endpoints**

### **Update Metadata**
```http
PUT http://localhost:8000/api/submissions/YOUR_SUBMISSION_ID/metadata
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
    "caption": "Updated caption!",
    "tags": ["freestyle", "updated"],
    "location": "Mumbai, India",
    "isPublic": true,
    "sharedToFeed": true,
    "highlightText": "Updated highlight text"
}
```

### **View Today's Challenge**
```http
GET http://localhost:8000/api/challenges/today
Authorization: Bearer YOUR_TOKEN
```

### **Search Challenges**
```http
GET http://localhost:8000/api/challenges/search?query=morning&type=freestyle&difficulty=beginner
Authorization: Bearer YOUR_TOKEN
```

### **View Leaderboard**
```http
GET http://localhost:8000/api/challenges/YOUR_CHALLENGE_ID/leaderboard?limit=10
Authorization: Bearer YOUR_TOKEN
```

## **🎯 Expected Response**

### **Successful Submission:**
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

## **🚨 Common Errors**

- **401 Unauthorized** - Check if token is valid
- **404 Challenge Not Found** - Verify challenge_id is correct
- **400 Already Submitted** - User can only submit once per challenge
- **413 File Too Large** - Reduce video file size

## **✅ Success Criteria**

- ✅ Can create challenge
- ✅ Can submit challenge with video
- ✅ Can check analysis status
- ✅ Can view submissions
- ✅ AI analysis completes successfully

---

**🎉 Your challenge system is ready for testing!**

## **📚 Additional Documentation**

- `API_DOCUMENTATION.md` - Complete API reference
- `S3_UPLOAD_GUIDE.md` - Detailed S3 implementation guide
- `GOOGLE_SIGNIN_SETUP.md` - Authentication setup 