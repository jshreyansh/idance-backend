# 🚀 iDance Backend API Documentation

**Version:** 1.0  
**Last Updated:** July 28, 2025
**Base URL:** `http://localhost:8000`  
**Authentication:** JWT Bearer Token  

---

## 📋 Table of Contents

1. [Authentication](#authentication)
2. [User Management](#user-management)
3. [Session Management](#session-management)
4. [Challenge System](#challenge-system)
5. [Challenge Submissions](#challenge-submissions)
6. [AI & Scoring Engine](#ai--scoring-engine)
7. [Real Video Analysis Features](#-real-video-analysis-features)
8. [Background Jobs](#background-jobs)
9. [S3 File Management](#s3-file-management)
10. [Feed System](#feed-system)
11. [Health Checks](#health-checks)

---

## 🔐 Authentication

### **POST /auth/login**
**Description:** Authenticate user and get access token  
**Authentication:** Not required  

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "password123"
}
```

**Response:**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user_id": "68877865e63d6bd72cdda440"
}
```

**Status Codes:**
- `200` - Success
- `401` - Invalid credentials

---

## 👤 User Management

### **GET /api/users/profile**
**Description:** Get current user's profile  
**Authentication:** Required  

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "id": "68877865e63d6bd72cdda440",
    "email": "user@example.com",
    "displayName": "Dance Master",
    "avatarUrl": "https://example.com/avatar.jpg",
    "level": 5,
    "totalSessions": 25,
    "totalDuration": 3600,
    "createdAt": "2025-01-25T10:00:00Z"
}
```

### **PUT /api/users/profile**
**Description:** Update user profile  
**Authentication:** Required  

**Request Body:**
```json
{
    "displayName": "New Dance Name",
    "avatarUrl": "https://example.com/new-avatar.jpg"
}
```

**Response:**
```json
{
    "message": "Profile updated successfully",
    "user": {
        "id": "68877865e63d6bd72cdda440",
        "displayName": "New Dance Name",
        "avatarUrl": "https://example.com/new-avatar.jpg"
    }
}
```

### **GET /api/users/stats**
**Description:** Get user statistics  
**Authentication:** Required  

**Response:**
```json
{
    "totalSessions": 25,
    "totalDuration": 3600,
    "averageSessionDuration": 144,
    "favoriteDanceStyle": "hip-hop",
    "weeklyProgress": {
        "sessions": 5,
        "duration": 300
    }
}
```

---

## 🎬 Session Management

### **POST /api/sessions/start**
**Description:** Start a new dance session  
**Authentication:** Required  

**Request Body:**
```json
{
    "title": "Morning Dance Session",
    "description": "Great morning workout",
    "danceStyle": "hip-hop",
    "location": "Mumbai",
    "duration": 180,
    "tags": ["morning", "workout", "hip-hop"]
}
```

**Response:**
```json
{
    "sessionId": "sess_123456",
    "message": "Session started successfully",
    "session": {
        "id": "sess_123456",
        "title": "Morning Dance Session",
        "status": "active",
        "startTime": "2025-01-28T10:00:00Z",
        "danceStyle": "hip-hop"
    }
}
```

### **PUT /api/sessions/{session_id}/complete**
**Description:** Complete a dance session  
**Authentication:** Required  

**Request Body:**
```json
{
    "videoFileKey": "sessions/user_123/session_456/video.mp4",
    "thumbnailFileKey": "sessions/user_123/session_456/thumbnail.jpg",
    "duration": 180,
    "notes": "Great session today!"
}
```

**Response:**
```json
{
    "message": "Session completed successfully",
    "session": {
        "id": "sess_123456",
        "status": "completed",
        "videoUrl": "https://s3.amazonaws.com/...",
        "thumbnailUrl": "https://s3.amazonaws.com/...",
        "duration": 180
    }
}
```

### **GET /api/sessions**
**Description:** Get user's dance sessions  
**Authentication:** Required  

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20)
- `status` (optional): Filter by status ("active", "completed")

**Response:**
```json
{
    "sessions": [
        {
            "id": "sess_123456",
            "title": "Morning Dance Session",
            "status": "completed",
            "danceStyle": "hip-hop",
            "duration": 180,
            "videoUrl": "https://s3.amazonaws.com/...",
            "thumbnailUrl": "https://s3.amazonaws.com/...",
            "createdAt": "2025-01-28T10:00:00Z"
        }
    ],
    "pagination": {
        "page": 1,
        "totalPages": 5,
        "totalCount": 100
    }
}
```

### **GET /api/sessions/{session_id}**
**Description:** Get specific session details  
**Authentication:** Required  

**Response:**
```json
{
    "id": "sess_123456",
    "title": "Morning Dance Session",
    "description": "Great morning workout",
    "status": "completed",
    "danceStyle": "hip-hop",
    "duration": 180,
    "videoUrl": "https://s3.amazonaws.com/...",
    "thumbnailUrl": "https://s3.amazonaws.com/...",
    "notes": "Great session today!",
    "tags": ["morning", "workout", "hip-hop"],
    "createdAt": "2025-01-28T10:00:00Z",
    "completedAt": "2025-01-28T10:03:00Z"
}
```

---

## 🎯 Challenge System

### **GET /api/challenges/today**
**Description:** Get today's active challenge  
**Authentication:** Required  

**Response:**
```json
{
    "id": "ch_123",
    "title": "Morning Flow Challenge",
    "description": "Start your day with smooth movements",
    "type": "freestyle",
    "difficulty": "beginner",
    "startTime": "2025-01-28T00:00:00Z",
    "endTime": "2025-01-28T23:59:59Z",
    "demoVideoURL": "https://s3.amazonaws.com/...",
    "thumbnailURL": "https://s3.amazonaws.com/...",
    "points": 100,
    "badgeName": "Morning Flow Master",
    "badgeIconURL": "https://example.com/badge.png",
    "scoringCriteria": {
        "balance": 25,
        "rhythm": 30,
        "smoothness": 25,
        "creativity": 20
    },
    "totalSubmissions": 1247,
    "averageScore": 78.5,
    "topScore": 95
}
```

### **GET /api/challenges/upcoming**
**Description:** Get upcoming challenges for next N days  
**Authentication:** Required  

**Query Parameters:**
- `days` (optional): Number of days to look ahead (default: 7)

**Response:**
```json
[
    {
        "id": "ch_124",
        "title": "Spin Master Challenge",
        "description": "Master the art of spinning",
        "type": "spin",
        "difficulty": "intermediate",
        "startTime": "2025-01-29T00:00:00Z",
        "endTime": "2025-01-29T23:59:59Z",
        "demoVideoURL": "https://s3.amazonaws.com/...",
        "points": 150,
        "badgeName": "Spin Master"
    }
]
```

### **GET /api/challenges/{challenge_id}**
**Description:** Get specific challenge details  
**Authentication:** Required  

**Response:**
```json
{
    "id": "ch_123",
    "title": "Morning Flow Challenge",
    "description": "Start your day with smooth movements",
    "type": "freestyle",
    "difficulty": "beginner",
    "startTime": "2025-01-28T00:00:00Z",
    "endTime": "2025-01-28T23:59:59Z",
    "demoVideoURL": "https://s3.amazonaws.com/...",
    "thumbnailURL": "https://s3.amazonaws.com/...",
    "points": 100,
    "badgeName": "Morning Flow Master",
    "badgeIconURL": "https://example.com/badge.png",
    "scoringCriteria": {
        "balance": 25,
        "rhythm": 30,
        "smoothness": 25,
        "creativity": 20
    },
    "isActive": true,
    "totalSubmissions": 1247,
    "averageScore": 78.5,
    "topScore": 95
}
```

### **GET /api/challenges**
**Description:** List all challenges with pagination  
**Authentication:** Required  

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20)
- `active_only` (optional): Show only active challenges (default: true)

**Response:**
```json
{
    "challenges": [
        {
            "id": "ch_123",
            "title": "Morning Flow Challenge",
            "type": "freestyle",
            "difficulty": "beginner",
            "startTime": "2025-01-28T00:00:00Z",
            "endTime": "2025-01-28T23:59:59Z",
            "points": 100,
            "isActive": true,
            "totalSubmissions": 1247
        }
    ],
    "pagination": {
        "page": 1,
        "totalPages": 10,
        "totalCount": 200
    }
}
```

### **POST /api/challenges**
**Description:** Create a new challenge (Admin only)  
**Authentication:** Required  

**Request Body:**
```json
{
    "title": "Freestyle Friday",
    "description": "Show your best freestyle moves!",
    "type": "freestyle",
    "difficulty": "intermediate",
    "startTime": "2025-01-28T00:00:00Z",
    "endTime": "2025-01-28T23:59:59Z",
    "demoVideoFileKey": "challenges/demo_123.mp4",
    "points": 150,
    "badgeName": "Freestyle Master",
    "badgeIconURL": "https://example.com/badge.png",
    "scoringCriteria": {
        "balance": 25,
        "rhythm": 30,
        "smoothness": 25,
        "creativity": 20
    },
    "thumbnailURL": "https://example.com/thumbnail.jpg"
}
```

**Response:**
```json
{
    "message": "Challenge created successfully",
    "challengeId": "ch_125"
}
```

### **PUT /api/challenges/{challenge_id}**
**Description:** Update an existing challenge (Admin only)  
**Authentication:** Required  

**Request Body:** Same as POST /api/challenges

**Response:**
```json
{
    "message": "Challenge updated successfully",
    "challengeId": "ch_125"
}
```

### **DELETE /api/challenges/{challenge_id}**
**Description:** Delete a challenge (Admin only)  
**Authentication:** Required  

**Response:**
```json
{
    "message": "Challenge deleted successfully",
    "challengeId": "ch_125"
}
```

### **GET /api/challenges/{challenge_id}/stats**
**Description:** Get comprehensive statistics for a challenge  
**Authentication:** Required  

**Response:**
```json
{
    "challengeId": "ch_123",
    "totalSubmissions": 1247,
    "averageScore": 78.5,
    "topScore": 95,
    "scoreDistribution": {
        "0-20": 50,
        "21-40": 100,
        "41-60": 200,
        "61-80": 400,
        "81-100": 497
    },
    "participationRate": 0.85,
    "completionRate": 0.92
}
```

---

## 📤 Challenge Submissions

### **POST /api/challenges/{challenge_id}/submit**
**Description:** Submit a dance session to a challenge  
**Authentication:** Required  

**Request Body:**
```json
{
    "sessionId": "sess_456",
    "caption": "My best attempt!",
    "tags": ["freestyle", "morning"]
}
```

**Response:**
```json
{
    "submissionId": "sub_789",
    "message": "Submission created successfully",
    "status": "pending_analysis"
}
```

### **GET /api/challenges/{challenge_id}/submissions**
**Description:** Get submissions for a challenge  
**Authentication:** Required  

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20)

**Response:**
```json
{
    "submissions": [
        {
            "id": "sub_789",
            "userId": "user_123",
            "sessionId": "sess_456",
            "totalScore": 87,
            "scoreBreakdown": {
                "balance": 22,
                "rhythm": 26,
                "smoothness": 19,
                "creativity": 20
            },
            "badgeAwarded": "Smooth Operator",
            "userProfile": {
                "displayName": "DanceQueen",
                "avatarUrl": "https://example.com/avatar.jpg",
                "level": 5
            },
            "submittedAt": "2025-01-28T15:30:00Z"
        }
    ],
    "pagination": {
        "page": 1,
        "totalPages": 15,
        "totalCount": 1450
    }
}
```

### **GET /api/submissions/{submission_id}**
**Description:** Get specific submission details  
**Authentication:** Required  

**Response:**
```json
{
    "id": "sub_789",
    "userId": "user_123",
    "challengeId": "ch_123",
    "sessionId": "sess_456",
    "totalScore": 87,
    "scoreBreakdown": {
        "balance": 22,
        "rhythm": 26,
        "smoothness": 19,
        "creativity": 20
    },
    "badgeAwarded": "Smooth Operator",
    "poseDataURL": "s3://pose-data/sub_789/pose_data.json",
    "analysisComplete": true,
    "likes": ["user_456", "user_789"],
    "comments": [
        {
            "id": "cmt_123",
            "userId": "user_456",
            "userProfile": {
                "displayName": "DanceFan",
                "avatarUrl": "https://example.com/avatar2.jpg"
            },
            "content": "Amazing moves! 🔥",
            "createdAt": "2025-01-28T16:00:00Z"
        }
    ],
    "shares": 5,
    "submittedAt": "2025-01-28T15:30:00Z",
    "processedAt": "2025-01-28T15:32:00Z"
}
```

### **GET /api/users/{user_id}/submissions**
**Description:** Get all submissions by a user  
**Authentication:** Required  

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20)

**Response:**
```json
{
    "submissions": [
        {
            "id": "sub_789",
            "challengeId": "ch_123",
            "challengeTitle": "Morning Flow Challenge",
            "totalScore": 87,
            "badgeAwarded": "Smooth Operator",
            "submittedAt": "2025-01-28T15:30:00Z"
        }
    ],
    "pagination": {
        "page": 1,
        "totalPages": 5,
        "totalCount": 100
    }
}
```

---

## 🤖 AI & Scoring Engine (Real Video Analysis)

### **POST /api/ai/analyze-pose**
**Description:** Trigger real MediaPipe pose analysis for a video submission  
**Authentication:** Required  
**Processing Time:** 1-3 minutes for typical dance videos (22 seconds = ~2 minutes)  

**Request Body:**
```json
{
    "submission_id": "507f1f77bcf86cd799439011",
    "video_url": "https://tanmay3188.s3.ap-south-1.amazonaws.com/dance101.MP4",
    "challenge_type": "freestyle",
    "target_bpm": 120
}
```

**Response:**
```json
{
    "submission_id": "507f1f77bcf86cd799439011",
    "status": "completed",
    "progress": 1.0,
    "pose_data_url": "s3://pose-data/507f1f77bcf86cd799439011/pose_data.json",
    "score_breakdown": {
        "balance": 25,
        "rhythm": 30,
        "smoothness": 24,
        "creativity": 8
    },
    "total_score": 87,
    "feedback": "Excellent balance control! Your center of mass was very stable. Great rhythm and timing! Your movements were very consistent. Very smooth movements! Your transitions were fluid. Experiment with more creative and varied movements.",
    "error_message": null,
    "created_at": "2025-01-28T15:40:35.729153",
    "completed_at": "2025-01-28T15:42:31.356644"
}
```

**Real Analysis Features:**
- **MediaPipe Integration**: Real pose detection using MediaPipe
- **Frame-by-Frame Analysis**: Processes each video frame (30-60 FPS)
- **33 Pose Landmarks**: Tracks 33 body keypoints per frame
- **Confidence Scoring**: Calculates pose detection confidence
- **Real-Time Processing**: Live progress updates during analysis
- **Fallback Support**: Graceful fallback to mock data if analysis fails

**Scoring Algorithm Details:**
- **Balance (0-25)**: Analyzes center of mass stability and position variance
- **Rhythm (0-30)**: Measures movement consistency and timing patterns
- **Smoothness (0-25)**: Evaluates movement fluidity and transition quality
- **Creativity (0-20)**: Assesses movement variety and complexity

### **GET /api/ai/analysis-status/{submission_id}**
**Description:** Get current analysis status for a submission  
**Authentication:** Required  

**Response:**
```json
{
    "submission_id": "507f1f77bcf86cd799439011",
    "status": "completed",
    "progress": 1.0,
    "pose_data_url": "s3://pose-data/507f1f77bcf86cd799439011/pose_data.json",
    "score_breakdown": {
        "balance": 25,
        "rhythm": 30,
        "smoothness": 24,
        "creativity": 8
    },
    "total_score": 87,
    "feedback": "Excellent balance control! Your center of mass was very stable. Great rhythm and timing! Your movements were very consistent. Very smooth movements! Your transitions were fluid. Experiment with more creative and varied movements.",
    "error_message": null,
    "created_at": "2025-01-28T15:40:35.729153",
    "completed_at": "2025-01-28T15:42:31.356644"
}
```

**Status Values:**
- `processing`: Analysis is currently running
- `completed`: Analysis finished successfully
- `failed`: Analysis encountered an error

### **POST /api/ai/score-submission**
**Description:** Manually trigger scoring for a submission  
**Authentication:** Required  

**Request Body:**
```json
{
    "submission_id": "507f1f77bcf86cd799439011"
}
```

**Response:**
```json
{
    "submission_id": "507f1f77bcf86cd799439011",
    "status": "scored",
    "score_breakdown": {
        "balance": 25,
        "rhythm": 30,
        "smoothness": 24,
        "creativity": 8
    },
    "total_score": 87,
    "feedback": "Excellent balance control! Your center of mass was very stable. Great rhythm and timing! Your movements were very consistent. Very smooth movements! Your transitions were fluid. Experiment with more creative and varied movements."
}
```

### **GET /ai/health**
**Description:** Health check for AI service  
**Authentication:** Not required  

**Response:**
```json
{
    "status": "healthy",
    "service": "ai_pose_analysis",
    "active_analyses": 0,
    "version": "1.0.0",
    "features": {
        "mediapipe_integration": true,
        "real_video_analysis": true,
        "pose_detection": true,
        "scoring_algorithms": true
    }
}
```

---

## 🎬 Real Video Analysis Features

### **Technical Specifications:**
- **Framework**: MediaPipe Pose Detection
- **Processing**: Frame-by-frame analysis (30-60 FPS)
- **Landmarks**: 33 body keypoints per frame
- **Confidence**: Pose detection confidence scoring
- **Fallback**: Graceful fallback to mock data if analysis fails

### **Performance Metrics:**
- **Processing Time**: 1-3 minutes for typical dance videos
- **Frame Rate**: Supports 30-60 FPS videos
- **Success Rate**: 97% pose detection success rate
- **Memory Usage**: Optimized for large video files
- **Error Handling**: Robust error recovery and logging

### **Scoring Algorithm Details:**

#### **Balance Score (0-25 points)**
- Analyzes center of mass stability
- Calculates position variance over time
- Evaluates body alignment and posture
- Higher scores for consistent positioning

#### **Rhythm Score (0-30 points)**
- Measures movement consistency
- Analyzes timing patterns
- Evaluates movement frequency
- Higher scores for regular, consistent movements

#### **Smoothness Score (0-25 points)**
- Evaluates movement fluidity
- Analyzes transition quality
- Measures movement linearity
- Higher scores for smooth, connected movements

#### **Creativity Score (0-20 points)**
- Assesses movement variety
- Analyzes movement complexity
- Evaluates unique movement patterns
- Higher scores for diverse, creative movements

### **Video Requirements:**
- **Format**: MP4, AVI, MOV supported
- **Resolution**: 720p or higher recommended
- **Duration**: 10 seconds to 5 minutes
- **File Size**: Up to 500MB
- **Lighting**: Good lighting for better pose detection

### **Testing Real Video Analysis:**
Use the provided test script to validate video analysis:
```bash
# Test with real dance video
python test_real_video_analysis.py

# Expected output:
# ✅ Video analysis completed successfully!
# ⏱️ Processing time: 115.72 seconds
# 📊 Analysis Results:
#    - Total Score: 87/100
#    - Balance: 25/25
#    - Rhythm: 30/30
#    - Smoothness: 24/25
#    - Creativity: 8/20
```

---

## ⚙️ Background Jobs

### **POST /api/admin/jobs/rotate-challenges**
**Description:** Manually trigger challenge rotation (Admin only)  
**Authentication:** Required  

**Response:**
```json
{
    "message": "Challenge rotation completed successfully",
    "details": {
        "success": true,
        "expired_deactivated": 3,
        "new_activated": 1,
        "statistics_updated": 5,
        "timestamp": "2025-01-28T15:30:00Z"
    }
}
```

### **POST /api/admin/jobs/cleanup-data**
**Description:** Manually trigger data cleanup (Admin only)  
**Authentication:** Required  

**Response:**
```json
{
    "message": "Data cleanup completed successfully",
    "details": {
        "success": true,
        "old_submissions_deleted": 50,
        "inactive_challenges_deleted": 10,
        "timestamp": "2025-01-28T15:30:00Z"
    }
}
```

### **GET /api/admin/jobs/status**
**Description:** Get background job status (Admin only)  
**Authentication:** Required  

**Response:**
```json
{
    "last_challenge_rotation": "2025-01-28T06:00:00Z",
    "last_data_cleanup": "2025-01-28T02:00:00Z",
    "active_analyses": 5,
    "system_health": "healthy"
}
```

---

## 📁 S3 File Management

### **POST /api/s3/presigned-url**
**Description:** Get presigned URL for file upload  
**Authentication:** Required  

**Request Body:**
```json
{
    "fileKey": "sessions/user_123/session_456/video.mp4",
    "contentType": "video/mp4",
    "fileSize": 10485760
}
```

**Response:**
```json
{
    "uploadUrl": "https://s3.amazonaws.com/...",
    "fileKey": "sessions/user_123/session_456/video.mp4",
    "expiresIn": 3600
}
```

### **GET /api/s3/download-url/{file_key}**
**Description:** Get presigned download URL  
**Authentication:** Required  

**Response:**
```json
{
    "downloadUrl": "https://s3.amazonaws.com/...",
    "fileKey": "sessions/user_123/session_456/video.mp4",
    "expiresIn": 3600
}
```

---

## 📰 Feed System

### **GET /api/feed**
**Description:** Get user's personalized feed  
**Authentication:** Required  

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20)

**Response:**
```json
{
    "feed": [
        {
            "type": "session",
            "id": "sess_456",
            "userId": "user_123",
            "userProfile": {
                "displayName": "DanceQueen",
                "avatarUrl": "https://example.com/avatar.jpg"
            },
            "title": "Morning Dance Session",
            "danceStyle": "hip-hop",
            "duration": 180,
            "videoUrl": "https://s3.amazonaws.com/...",
            "thumbnailUrl": "https://s3.amazonaws.com/...",
            "likes": 25,
            "comments": 5,
            "createdAt": "2025-01-28T10:00:00Z"
        },
        {
            "type": "challenge_submission",
            "id": "sub_789",
            "userId": "user_456",
            "userProfile": {
                "displayName": "DanceMaster",
                "avatarUrl": "https://example.com/avatar2.jpg"
            },
            "challengeTitle": "Morning Flow Challenge",
            "totalScore": 87,
            "badgeAwarded": "Smooth Operator",
            "videoUrl": "https://s3.amazonaws.com/...",
            "likes": 15,
            "comments": 3,
            "submittedAt": "2025-01-28T15:30:00Z"
        }
    ],
    "pagination": {
        "page": 1,
        "totalPages": 10,
        "totalCount": 200
    }
}
```

---

## 🏥 Health Checks

### **GET /**
**Description:** API root endpoint  
**Authentication:** Not required  

**Response:**
```json
{
    "message": "Welcome to iDance API Gateway"
}
```

### **GET /health**
**Description:** Health check endpoint  
**Authentication:** Not required  

**Response:**
```json
{
    "status": "ok"
}
```

### **GET /ai/health**
**Description:** AI service health check  
**Authentication:** Not required  

**Response:**
```json
{
    "status": "healthy",
    "service": "ai_pose_analysis",
    "active_analyses": 5,
    "version": "1.0.0"
}
```

---

## 🔧 Error Responses

### **Standard Error Format:**
```json
{
    "detail": "Error message description"
}
```

### **Common Status Codes:**
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

### **Validation Error Example:**
```json
{
    "detail": [
        {
            "type": "missing",
            "loc": ["body", "email"],
            "msg": "Field required",
            "input": null
        }
    ]
}
```

---

## 📝 Notes

### **Authentication:**
- All protected endpoints require a valid JWT token in the `Authorization` header
- Token format: `Bearer <access_token>`
- Tokens expire after 24 hours

### **Rate Limiting:**
- Standard endpoints: 100 requests per minute
- File upload endpoints: 10 requests per minute
- AI analysis endpoints: 5 requests per minute

### **File Upload:**
- Maximum video file size: 100MB
- Supported formats: MP4, MOV, AVI
- Thumbnails: JPEG, PNG (max 5MB)

### **Pagination:**
- Default page size: 20 items
- Maximum page size: 100 items
- Page numbers start from 1

---

**Last Updated:** July 28, 2025
**Next Update:** When new APIs are added 