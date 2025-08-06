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
7. [Dance Breakdown System](#dance-breakdown-system)
8. [Real Video Analysis Features](#-real-video-analysis-features)
9. [Background Jobs](#background-jobs)
10. [S3 File Management](#s3-file-management)
11. [Feed System](#feed-system)
12. [Health Checks](#health-checks)

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

---

## 🎬 Dance Breakdown System

### **POST /api/ai/dance-breakdown**
**Description:** Create step-by-step dance breakdown from YouTube/Instagram URL  
**Authentication:** Required  

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "video_url": "https://www.youtube.com/watch?v=example",
    "mode": "auto",
    "target_difficulty": "beginner"
}
```

**Response:**
```json
{
    "success": true,
    "video_url": "https://www.youtube.com/watch?v=example",
    "playable_video_url": "https://idanceshreyansh.s3.ap-south-1.amazonaws.com/dance-breakdowns/user123/20250125_143022_abc12345.mp4",
    "title": "Dance Video Analysis",
    "duration": 30.0,
    "bpm": 120.5,
    "difficulty_level": "Intermediate",
    "total_steps": 8,
    "routine_analysis": {
        "bpm": 120.5,
        "total_segments": 8,
        "style_indicators": {
            "rhythm_consistency": "High",
            "flow_smoothness": "Medium",
            "symmetry": "Balanced"
        },
        "difficulty_level": "Intermediate",
        "energy_level": "Medium",
        "overall_routine_characteristics": {
            "tempo": "The routine is set to a moderate tempo of 120.5 BPM",
            "rhythm_consistency": "The routine maintains a steady beat",
            "flow_smoothness": "Transitions between movements are fluid",
            "symmetry": "The routine has a good balance between left and right movements",
            "difficulty_level": "Suitable for dancers with some experience",
            "energy_level": "Engaging and dynamic without being overly exhausting"
        }
    },
    "steps": [
        {
            "step_number": 1,
            "start_timestamp": "00:00.000",
            "end_timestamp": "00:02.460",
            "step_name": "Right Hand Flourish",
            "global_description": "Start with a graceful flourish of your right hand, moving it elegantly from the wrist and fingers.",
            "description": {
                "head": "Keep your head facing forward, with a slight tilt to the right to follow the hand movement.",
                "hands": "Extend your right hand outwards, starting with the pinky and moving through the index and thumb. Let your wrist and elbow follow in a fluid motion.",
                "shoulders": "Relax your shoulders, allowing the right shoulder to drop slightly as your hand moves.",
                "torso": "Maintain a straight posture, with a slight lean to the right to complement the hand movement.",
                "legs": "Keep your legs steady and slightly apart for balance.",
                "bodyAngle": "Face forward with a slight angle to the right, aligning with the hand movement."
            },
            "style_and_history": "This movement is a modern fusion, often seen in contemporary dance where expressive hand movements are used to convey emotion.",
            "spice_it_up": "Add a gentle wrist flick at the end for a touch of flair.",
            "connection_to_next": "This hand flourish naturally leads into the next step by shifting your weight to the left foot.",
            "technical_notes": {
                "alignment": "Maintain neutral spine alignment",
                "timing": "Follow the beat of the music",
                "energy": "Keep movements fluid and controlled",
                "precision": "Focus on clean hand positioning"
            },
            "quality_metrics": {
                "smoothness": "High",
                "stability": "Good",
                "precision": "Excellent",
                "energy": "Moderate",
                "balance": "Maintained"
            }
        }
    ],
    "outline_url": "http://localhost:8000/videos/default_outline.mp4",
    "mode": "auto",
    "error_message": null
}
```

**Status Codes:**
- `200` - Success
- `400` - Invalid request
- `401` - Unauthorized
- `500` - Processing error

### **GET /api/ai/dance-breakdowns**
**Description:** Get user's dance breakdown history with pagination  
**Authentication:** Required  

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `limit` (optional, default: 20): Number of breakdowns to return
- `skip` (optional, default: 0): Number of breakdowns to skip

**Response:**
```json
{
    "success": true,
    "total": 5,
    "breakdowns": [
        {
            "_id": "677f1f77bcf86cd799439011",
            "videoUrl": "https://www.youtube.com/shorts/example",
            "title": "Dance Video Analysis",
            "mode": "manual",
            "targetDifficulty": "beginner",
            "duration": 30.0,
            "bpm": 120.5,
            "difficultyLevel": "Intermediate",
            "totalSteps": 15,
            "success": true,
            "createdAt": "2024-01-15T10:30:00Z"
        }
    ],
    "pagination": {
        "limit": 20,
        "skip": 0,
        "has_more": false
    }
}
```

### **GET /api/ai/dance-breakdown/{breakdown_id}**
**Description:** Get specific dance breakdown by ID (full details)  
**Authentication:** Required  

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "_id": "677f1f77bcf86cd799439011",
    "userId": "677f1f77bcf86cd799439012",
    "videoUrl": "https://www.youtube.com/shorts/example",
    "title": "Dance Video Analysis",
    "mode": "manual",
    "targetDifficulty": "beginner",
    "duration": 30.0,
    "bpm": 120.5,
    "difficultyLevel": "Intermediate",
    "totalSteps": 15,
    "routineAnalysis": {...},
    "steps": [
        {
            "step_number": 1,
            "start_timestamp": "00:00.000",
            "end_timestamp": "00:02.000",
            "step_name": "Opening Move",
            "global_description": "Start with confidence",
            "description": {
                "head": "Keep centered",
                "hands": "Relaxed at sides",
                "shoulders": "Level and back",
                "torso": "Engaged core",
                "legs": "Hip-width stance",
                "bodyAngle": "Face forward"
            },
            "style_and_history": "Contemporary fusion",
            "spice_it_up": "Add personal flair"
        }
    ],
    "outlineUrl": "http://localhost:8000/videos/outline.mp4",
    "success": true,
    "createdAt": "2024-01-15T10:30:00Z",
    "updatedAt": "2024-01-15T10:30:00Z"
}
```

**Status Codes:**
- `200` - Success
- `404` - Breakdown not found or not owned by user
- `401` - Unauthorized

### **GET /api/ai/dance-breakdowns/videos**
**Description:** Get all breakdown videos for the input screen  
**Authentication:** Required  

**Parameters:**
- `page` (query): Page number (default: 1)
- `limit` (query): Items per page (default: 20)

**Response:**
```json
{
    "breakdowns": [
        {
            "id": "68936a1f93b74bc4f0112219",
            "videoUrl": "https://www.youtube.com/watch?v=example",
            "playableVideoUrl": "https://idanceshreyansh.s3.ap-south-1.amazonaws.com/dance-breakdowns/user123/20250125_143022_abc12345.mp4",
            "thumbnailUrl": "https://idanceshreyansh.s3.ap-south-1.amazonaws.com/dance-breakdowns/user123/20250125_143022_abc12345_thumb.jpg",
            "title": "Hip Hop Dance Breakdown",
            "duration": 180.5,
            "durationFormatted": "3:00",
            "bpm": 120.5,
            "difficultyLevel": "Intermediate",
            "totalSteps": 8,
            "success": true,
            "createdAt": "2025-01-25T14:30:22Z",
            "userProfile": {
                "displayName": "Dance Master",
                "avatarUrl": "https://example.com/avatar.jpg",
                "level": 5
            }
        }
    ],
    "total": 25,
    "page": 1,
    "limit": 20,
    "hasMore": true
}
```

---

## 🤖 AI & Scoring Engine

### **POST /api/ai/analyze-pose**
**Description:** Trigger pose analysis for a video submission  
**Authentication:** Required  

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "submission_id": "68877865e63d6bd72cdda440",
    "video_url": "https://example.com/video.mp4",
    "challenge_type": "freestyle",
    "target_bpm": 120
}
```

**Response:**
```json
{
    "submission_id": "68877865e63d6bd72cdda440",
    "status": "completed",
    "progress": 1.0,
    "pose_data_url": "s3://pose-data/68877865e63d6bd72cdda440/pose_data.json",
    "score_breakdown": {
        "balance": 20,
        "rhythm": 25,
        "smoothness": 22,
        "creativity": 18
    },
    "total_score": 85,
    "feedback": "Excellent performance! Your balance and rhythm were particularly strong...",
    "created_at": "2025-01-25T10:00:00Z",
    "completed_at": "2025-01-25T10:05:00Z"
}
```

### **GET /api/ai/analysis-status/{submission_id}**
**Description:** Get current analysis status for a submission  
**Authentication:** Required  

**Response:**
```json
{
    "submission_id": "68877865e63d6bd72cdda440",
    "status": "processing",
    "progress": 0.75,
    "created_at": "2025-01-25T10:00:00Z"
}
```

### **POST /api/ai/score-submission**
**Description:** Manually trigger scoring for a submission  
**Authentication:** Required  

**Request Body:**
```json
{
    "submission_id": "68877865e63d6bd72cdda440"
}
```

**Response:**
```json
{
    "submission_id": "68877865e63d6bd72cdda440",
    "status": "scored",
    "score_breakdown": {
        "balance": 20,
        "rhythm": 25,
        "smoothness": 22,
        "creativity": 18
    },
    "total_score": 85,
    "feedback": "Excellent performance! Your balance and rhythm were particularly strong..."
}
```

---

## 🎯 Real Video Analysis Features

### **Enhanced Pose Detection**
- **MediaPipe Integration**: Real-time pose estimation using MediaPipe
- **Multi-frame Analysis**: Processes video at 15 FPS for accuracy
- **Joint Tracking**: Tracks 33 body landmarks with confidence scores
- **Movement Segmentation**: Uses ruptures library for change-point detection

### **Movement Analysis**
- **Joint Angles**: Calculates angles between connected joints
- **Velocity Analysis**: Tracks movement speed and acceleration
- **Pattern Recognition**: Identifies movement patterns and transitions
- **Quality Metrics**: Smoothness, stability, precision, energy, balance

### **Rhythm Analysis**
- **BPM Detection**: Uses librosa for audio tempo analysis
- **Beat Synchronization**: Aligns movements with musical beats
- **Rhythm Consistency**: Measures timing accuracy and consistency

### **Scoring System**
- **Balance (0-25)**: Posture and stability assessment
- **Rhythm (0-30)**: Musical timing and beat synchronization
- **Smoothness (0-25)**: Movement fluidity and transitions
- **Creativity (0-20)**: Artistic expression and originality

---

## 🔄 Background Jobs

### **POST /api/background/jobs/pose-analysis**
**Description:** Queue pose analysis job  
**Authentication:** Required  

**Request Body:**
```json
{
    "submission_id": "68877865e63d6bd72cdda440",
    "video_url": "https://example.com/video.mp4"
}
```

**Response:**
```json
{
    "job_id": "job_123456",
    "status": "queued",
    "estimated_duration": 300
}
```

### **GET /api/background/jobs/{job_id}**
**Description:** Get job status  
**Authentication:** Required  

**Response:**
```json
{
    "job_id": "job_123456",
    "status": "processing",
    "progress": 0.75,
    "estimated_completion": "2025-01-25T10:05:00Z"
}
```

---

## ☁️ S3 File Management

### **POST /api/s3/upload**
**Description:** Upload file to S3  
**Authentication:** Required  

**Request Body:**
```json
{
    "file": "binary_data",
    "filename": "dance_video.mp4",
    "content_type": "video/mp4"
}
```

**Response:**
```json
{
    "file_url": "https://s3.amazonaws.com/bucket/filename.mp4",
    "file_key": "uploads/user_id/filename.mp4",
    "size": 1024000
}
```

### **DELETE /api/s3/delete/{file_key}**
**Description:** Delete file from S3  
**Authentication:** Required  

**Response:**
```json
{
    "message": "File deleted successfully",
    "file_key": "uploads/user_id/filename.mp4"
}
```

---

## 📰 Feed System

### **GET /api/feed**
**Description:** Get user feed  
**Authentication:** Required  

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `limit` (int): Items per page (default: 20)
- `type` (string): Filter by content type

**Response:**
```json
{
    "items": [
        {
            "id": "feed_item_123",
            "type": "submission",
            "user": {
                "id": "68877865e63d6bd72cdda440",
                "displayName": "Dance Master",
                "avatarUrl": "https://example.com/avatar.jpg"
            },
            "content": {
                "video_url": "https://example.com/video.mp4",
                "thumbnail_url": "https://example.com/thumbnail.jpg",
                "title": "Amazing Freestyle Performance",
                "score": 85
            },
            "created_at": "2025-01-25T10:00:00Z"
        }
    ],
    "pagination": {
        "page": 1,
        "limit": 20,
        "total": 150,
        "pages": 8
    }
}
```

---

## 🏥 Health Checks

### **GET /health**
**Description:** Basic health check  
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
    "status": "ai service ok"
}
```

---

## 🔧 Error Handling

All endpoints return consistent error responses:

**Error Response Format:**
```json
{
    "detail": "Error message description"
}
```

**Common Status Codes:**
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found (resource doesn't exist)
- `422` - Validation Error (invalid request body)
- `500` - Internal Server Error (server-side error)

---

## 📝 Notes

### **Authentication**
- All protected endpoints require a valid JWT token
- Include token in Authorization header: `Bearer <token>`
- Tokens expire after 24 hours

### **Rate Limiting**
- API calls are limited to 100 requests per minute per user
- Background jobs have separate rate limits

### **File Uploads**
- Maximum file size: 100MB for videos
- Supported formats: MP4, MOV, AVI
- Files are automatically processed and optimized

### **Dance Breakdown Features**
- Supports YouTube and Instagram video URLs
- Automatic BPM detection from audio
- Step-by-step movement analysis
- OpenAI-powered step descriptions
- Manual and automatic processing modes 

### **POST /api/challenges**
**Description:** Create a new challenge (admin only)  
**Authentication:** Required  

**Request Body:**
```json
{
    "title": "Freestyle Friday",
    "description": "Show your freestyle moves!",
    "type": "freestyle",
    "difficulty": "intermediate",
    "startTime": "2025-01-25T00:00:00Z",
    "endTime": "2025-01-26T23:59:59Z",
    "demoVideoURL": "https://example.com/demo.mp4",
    "points": 100,
    "badgeName": "Freestyle Master",
    "badgeIconURL": "https://example.com/badge.png",
    "categories": ["hip hop", "trendy"],
    "tags": ["freestyle", "challenge"]
}
```

**Response:**
```json
{
    "message": "Challenge created successfully",
    "challenge_id": "688b8ef5643bcb1dffaa85f7"
}
```

### **GET /api/challenges/{challenge_id}/leaderboard**
**Description:** Get leaderboard for a specific challenge  
**Authentication:** Required  

**Parameters:**
- `challenge_id` (path): Challenge ID

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "challengeId": "68885e917dcfd112158b2a10",
    "challengeTitle": "Freestyle Friday",
    "entries": [
        {
            "rank": 1,
            "userId": "68877865e63d6bd72cdda440",
            "userProfile": {
                "displayName": "Dance Master",
                "avatarUrl": "https://example.com/avatar.jpg",
                "level": 5
            },
            "score": 95,
            "scoreBreakdown": {
                "balance": 25,
                "rhythm": 30,
                "smoothness": 25,
                "creativity": 15
            },
            "submittedAt": "2025-01-25T10:00:00Z",
            "submissionId": "68885e917dcfd112158b2a11"
        }
    ],
    "total": 25,
    "userRank": 3
}
```

### **GET /api/challenges/{challenge_id}/public-submissions**
**Description:** Get public submissions for a specific challenge with video URLs  
**Authentication:** Required  

**Parameters:**
- `challenge_id` (path): Challenge ID
- `page` (query): Page number (default: 1)
- `limit` (query): Items per page (default: 20)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "challengeId": "68885e917dcfd112158b2a10",
    "challengeTitle": "Freestyle Friday",
    "submissions": [
        {
            "id": "68885e917dcfd112158b2a11",
            "userId": "68877865e63d6bd72cdda440",
            "userProfile": {
                "displayName": "Dance Master",
                "avatarUrl": "https://example.com/avatar.jpg",
                "level": 5
            },
            "video": {
                "url": "https://idanceshreyansh.s3.ap-south-1.amazonaws.com/challenges/user123/challenge456/20250128_153000_abc12345.mp4",
                "file_key": "challenges/user123/challenge456/20250128_153000_abc12345.mp4",
                "duration": 120,
                "size_mb": 25.5
            },
            "analysis": {
                "status": "completed",
                "score": 95,
                "breakdown": {
                    "balance": 25,
                    "rhythm": 30,
                    "smoothness": 25,
                    "creativity": 15
                },
                "feedback": "Great rhythm and balance!",
                "confidence": 0.92
            },
            "metadata": {
                "caption": "My freestyle challenge attempt!",
                "tags": ["freestyle", "challenge"],
                "location": "Mumbai, India",
                "isPublic": true,
                "sharedToFeed": true,
                "highlightText": "Check out my moves!"
            },
            "submittedAt": "2025-01-25T10:00:00Z",
            "likes": ["user1", "user2"],
            "comments": [
                {
                    "userId": "user1",
                    "text": "Amazing moves!",
                    "timestamp": "2025-01-25T10:30:00Z"
                }
            ],
            "shares": 5
        }
    ],
    "total": 25,
    "page": 1,
    "limit": 20
}
```

**Status Codes:**
- `200` - Success
- `404` - Challenge not found
- `401` - Unauthorized 

### **GET /api/challenges/categories**
**Description:** Get all available challenge categories  
**Authentication:** Required  

**Response:**
```json
[
    "hip hop",
    "ballet",
    "trendy",
    "party",
    "sexy",
    "contemporary",
    "jazz",
    "street",
    "latin",
    "afro",
    "bollywood",
    "k-pop",
    "freestyle",
    "choreography"
]
```

### **GET /api/challenges/category/{category}**
**Description:** Get challenges by specific category  
**Authentication:** Required  

**Parameters:**
- `category` (path): Category name (e.g., "hip hop", "trendy")
- `page` (query): Page number (default: 1)
- `limit` (query): Items per page (default: 20)
- `active_only` (query): Show only active challenges (default: true)

**Response:**
```json
{
    "challenges": [
        {
            "id": "688b8ef5643bcb1dffaa85f7",
            "title": "Freestyle Friday",
            "description": "Show your freestyle moves!",
            "type": "freestyle",
            "difficulty": "intermediate",
            "categories": ["hip hop", "trendy"],
            "tags": ["freestyle", "challenge"],
            "points": 100,
            "badgeName": "Freestyle Master",
            "badgeIconURL": "https://example.com/badge.png",
            "isActive": true,
            "totalSubmissions": 25,
            "participantCount": 25
        }
    ],
    "total": 1,
    "page": 1,
    "limit": 20
}
``` 

### **GET /api/activities/me**
**Description:** Get all user activities (sessions, challenges, breakdowns) unified  
**Authentication:** Required  

**Parameters:**
- `page` (query): Page number (default: 1)
- `limit` (query): Items per page (default: 20)
- `activity_type` (query): Filter by activity type - 'sessions', 'challenges', 'breakdowns', or None for all (default: None)

**Response:**
```json
{
    "activities": [
        {
            "_id": "6893835c1ef74973896e2bf3",
            "activityType": "challenge",
            "activityDate": "2025-08-06T16:31:23.000Z",
            "title": "Challenge Submission",
            "description": "5 minutes • 45 calories",
            "videoUrl": "https://idanceshreyansh.s3.ap-south-1.amazonaws.com/...",
            "durationMinutes": 5,
            "caloriesBurned": 45,
            "score": 85,
            "isPublic": true
        },
        {
            "_id": "6893823c1515c715f0ae3f96",
            "activityType": "breakdown",
            "activityDate": "2025-08-06T16:26:36.000Z",
            "title": "Dance Breakdown",
            "description": "5 steps • Intermediate",
            "videoUrl": "https://www.youtube.com/shorts/4ybhF5fK2bo",
            "duration": 30.0,
            "totalSteps": 5,
            "difficultyLevel": "Intermediate",
            "success": true
        },
        {
            "_id": "68937e749523ddad93840789",
            "activityType": "session",
            "activityDate": "2025-08-06T16:10:28.000Z",
            "title": "Hip Hop Session",
            "description": "15 minutes • 120 calories",
            "startTime": "2025-08-06T16:10:28.000Z",
            "endTime": "2025-08-06T16:25:28.000Z",
            "style": "hip hop",
            "sessionType": "freestyle",
            "durationMinutes": 15,
            "caloriesBurned": 120,
            "isPublic": true,
            "videoThumbnailUrl": "https://...",
            "likesCount": 5,
            "commentsCount": 2,
            "status": "completed"
        }
    ],
    "total": 3,
    "page": 1,
    "limit": 20,
    "hasMore": false,
    "counts": {
        "sessions": 8,
        "challenges": 5,
        "breakdowns": 7,
        "total": 20
    }
}
```

### **GET /api/sessions/me** 