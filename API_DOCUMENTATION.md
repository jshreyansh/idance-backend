# 🚀 iDance Backend API Documentation

**Version:** 1.0  
**Last Updated:** July 28, 2025
**Base URL:** `http://localhost:8000`  
**Authentication:** JWT Bearer Token  

---

## 📋 Table of Contents

1. [Authentication](#authentication)
2. [User Management](#user-management)
3. [User Statistics](#user-statistics)
4. [Session Management](#session-management)
5. [Challenge System](#challenge-system)
6. [Challenge Submissions](#challenge-submissions)
7. [AI & Scoring Engine](#ai--scoring-engine)
8. [Dance Breakdown System](#dance-breakdown-system)
9. [Real Video Analysis Features](#-real-video-analysis-features)
10. [Background Jobs](#background-jobs)
11. [S3 File Management](#s3-file-management)
12. [Feed System](#feed-system)
13. [Health Checks](#health-checks)

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

### **POST /auth/signup**
**Description:** Register new user with email/password  
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
    "message": "Signup successful",
    "user_id": "68877865e63d6bd72cdda440",
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
}
```

**Status Codes:**
- `200` - Success
- `400` - Email already registered

### **POST /auth/google**
**Description:** Authenticate user with Google OAuth  
**Authentication:** Not required  

**Request Body:**
```json
{
    "idToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "accessToken": "ya29.a0AfH6SMC..."
}
```

**Response:**
```json
{
    "message": "Google sign-in successful",
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user_id": "68877865e63d6bd72cdda440",
    "user": {
        "email": "user@gmail.com",
        "name": "John Doe",
        "picture": "https://lh3.googleusercontent.com/...",
        "email_verified": true
    }
}
```

**Status Codes:**
- `200` - Success
- `400` - Invalid token
- `500` - Internal server error

**Notes:**
- Automatically generates unique username from user's name
- Fetches extended profile data (gender, birth year, phone, location) from Google People API
- Supports both ID token and access token fallback authentication

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

## 📊 User Statistics

### **GET /api/stats/me**
**Description:** Get comprehensive user statistics calculated from actual activity data  
**Authentication:** Required  

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "totalActivities": 45,
    "totalSessions": 20,
    "totalChallenges": 15,
    "totalBreakdowns": 10,
    "totalKcal": 2500,
    "totalTimeMinutes": 180,
    "totalSteps": 5000,
    "currentStreakDays": 7,
    "maxStreakDays": 15,
    "lastActiveDate": "2025-01-25",
    "level": 5,
    "starsEarned": 150,
    "rating": 85,
    "mostPlayedStyle": "hip hop",
    "trophies": ["first_place", "streak_master"],
    "weeklyActivity": [
        {
            "date": "2025-01-25",
            "activitiesCount": 5
        },
        {
            "date": "2025-01-24",
            "activitiesCount": 3
        }
    ]
}
```

**Notes:**
- **Fitness metrics** (totalKcal, totalTimeMinutes, totalSteps, starsEarned) are calculated from actual activity data
- **Sessions**: Calories and duration from completed sessions
- **Challenges**: Calories calculated based on challenge type and video duration
  - Freestyle: 5 calories/minute
  - Static: 3 calories/minute  
  - Other: 4 calories/minute
- **Dance Breakdowns**: Calories calculated at 4 calories/minute for analysis activity
- **Activity counts** are real-time calculated from database

### **POST /api/stats/update**
**Description:** Update user statistics manually  
**Authentication:** Required  

**Request Body:**
```json
{
    "kcal": 100,
    "minutes": 15,
    "steps": 500,
    "stars": 5,
    "style": "hip hop"
}
```

**Response:**
```json
{
    "message": "Stats updated"
}
```

### **GET /api/stats/heatmap**
**Description:** Get activity heatmap data showing total activities (sessions + challenges + breakdowns) per day  
**Authentication:** Required  

**Query Parameters:**
- `days` (int): Number of days to include (default: 7)

**Response:**
```json
[
    {
        "date": "2025-01-25",
        "activitiesCount": 5,
        "isActive": true,
        "caloriesBurned": 150
    },
    {
        "date": "2025-01-24",
        "activitiesCount": 3,
        "isActive": true,
        "caloriesBurned": 100
    }
]
```

**Notes:**
- `activitiesCount` includes sessions, challenges, and dance breakdowns
- `caloriesBurned` only includes calories from dance sessions (challenges and breakdowns don't track calories)
- `isActive` is true when there are any activities on that day

---

## 🎬 Session Management

### **POST /api/sessions/start**
**Description:** Start a new dance session  
**Authentication:** Required  

**Request Body:**
```json
{
    "style": "hip hop",
    "sessionType": "freestyle",
    "isPublic": true,
    "sharedToFeed": false,
    "remixable": false,
    "promptUsed": "Dance to the beat",
    "inspirationSessionId": "68877865e63d6bd72cdda440",
    "location": "New York",
    "highlightText": "Amazing session!",
    "tags": ["energetic", "fun"]
}
```

**Response:**
```json
{
    "sessionId": "68877865e63d6bd72cdda440"
}
```

### **POST /api/sessions/complete**
**Description:** Complete a dance session with optional video processing  
**Authentication:** Required  

**Request Body:**
```json
{
    "sessionId": "68877865e63d6bd72cdda440",
    "endTime": "2025-01-25T10:30:00Z",
    "durationMinutes": 15,
    "caloriesBurned": 120,
    "videoURL": "https://s3.amazonaws.com/bucket/video.mp4",
    "videoFileKey": "sessions/user_id/session_id/video.mp4",
    "thumbnailURL": "https://s3.amazonaws.com/bucket/thumbnail.jpg",
    "thumbnailFileKey": "sessions/user_id/session_id/thumbnail.jpg",
    "score": 85,
    "stars": 4,
    "rating": 4.5,
    "highlightText": "Amazing dance session!",
    "tags": ["hip hop", "energetic"],
    "cropData": {
        "aspectRatio": 1.0,
        "videoDimensions": {"width": 1920, "height": 1080},
        "cropTemplate": "square"
    }
}
```

**Crop Templates:**
- `"square"`: Crop to 1:1 aspect ratio
- `"portrait"`: Crop to 9:16 aspect ratio  
- `"landscape"`: Crop to 16:9 aspect ratio

**Response:**
```json
{
    "message": "Session completed successfully with video processing"
}
```

**Processing Status:**
- `"not_required"`: No video processing needed
- `"processing"`: Video is being processed
- `"completed"`: Video processing successful
- `"failed"`: Video processing failed (original video used)

### **GET /api/sessions/me**
**Description:** Get user's dance sessions  
**Authentication:** Required  

**Response:**
```json
[
    {
        "_id": "68877865e63d6bd72cdda440",
        "userId": "68877865e63d6bd72cdda441",
        "startTime": "2025-01-25T10:00:00Z",
        "endTime": "2025-01-25T10:30:00Z",
        "status": "completed",
        "durationMinutes": 30,
        "caloriesBurned": 150,
        "style": "hip hop",
        "sessionType": "freestyle",
        "videoURL": "https://s3.amazonaws.com/bucket/video.mp4",
        "processedVideoURL": "https://s3.amazonaws.com/bucket/cropped_video.mp4",
        "thumbnailURL": "https://s3.amazonaws.com/bucket/thumbnail.jpg",
        "score": 85,
        "stars": 4,
        "rating": 4.5,
        "highlightText": "Amazing session!",
        "tags": ["energetic", "fun"],
        "isPublic": true,
        "sharedToFeed": false,
        "remixable": false,
        "cropData": {
            "aspectRatio": 1.0,
            "videoDimensions": {"width": 1920, "height": 1080},
            "cropTemplate": "square"
        },
        "processingStatus": "completed",
        "createdAt": "2025-01-25T10:00:00Z",
        "updatedAt": "2025-01-25T10:30:00Z"
    }
]
```

### **GET /api/sessions/feed**
**Description:** Get public dance sessions feed  
**Authentication:** Required  

**Query Parameters:**
- `style` (optional): Filter by dance style
- `location` (optional): Filter by location
- `skip` (optional, default: 0): Number of sessions to skip
- `limit` (optional, default: 20): Number of sessions to return

**Response:**
```json
[
    {
        "_id": "68877865e63d6bd72cdda440",
        "userId": "68877865e63d6bd72cdda441",
        "userProfile": {
            "displayName": "Dance Master",
            "avatarUrl": "https://example.com/avatar.jpg",
            "isPro": false,
            "location": "New York"
        },
        "startTime": "2025-01-25T10:00:00Z",
        "endTime": "2025-01-25T10:30:00Z",
        "durationMinutes": 30,
        "caloriesBurned": 150,
        "style": "hip hop",
        "sessionType": "freestyle",
        "videoURL": "https://s3.amazonaws.com/bucket/video.mp4",
        "processedVideoURL": "https://s3.amazonaws.com/bucket/cropped_video.mp4",
        "thumbnailURL": "https://s3.amazonaws.com/bucket/thumbnail.jpg",
        "score": 85,
        "stars": 4,
        "rating": 4.5,
        "highlightText": "Amazing session!",
        "tags": ["energetic", "fun"],
        "likesCount": 5,
        "commentsCount": 2,
        "createdAt": "2025-01-25T10:00:00Z"
    }
]
```

---

## 🎬 Dance Breakdown System

### **POST /api/s3/upload/dance-breakdown-video**
**Description:** Get presigned URL for uploading video for dance breakdown analysis  
**Authentication:** Required  

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "file_extension": "mp4",
    "content_type": "video/mp4",
    "file_size_mb": 25.5,
    "original_filename": "my_dance_video.mp4"
}
```

**File Size Limits:**
- **Maximum**: 100MB
- **Minimum**: 0.1MB (100KB)
- **Recommended**: 5-50MB for optimal processing

**Response:**
```json
{
    "upload_url": "https://s3.amazonaws.com/presigned-upload-url",
    "file_key": "dance-breakdowns/user123/breakdown456/original_video.mp4",
    "content_type": "video/mp4",
    "expires_in": 3600,
    "file_url": "https://bucket.s3.region.amazonaws.com/dance-breakdowns/user123/breakdown456/original_video.mp4",
    "breakdown_id": "breakdown456"
}
```

### **POST /api/ai/dance-breakdown**
**Description:** Create step-by-step dance breakdown from YouTube/Instagram URL or uploaded video  
**Authentication:** Required  

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body (URL):**
```json
{
    "video_url": "https://www.youtube.com/watch?v=example",
    "mode": "auto",
    "target_difficulty": "beginner"
}
```

**Request Body (Uploaded Video):**
```json
{
    "video_url": "https://bucket.s3.region.amazonaws.com/dance-breakdowns/user123/breakdown456/original_video.mp4",
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

### **POST /api/ai/dance-breakdowns/regenerate-thumbnails**
**Description:** Regenerate thumbnails for existing dance breakdowns that don't have them  
**Authentication:** Required  

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "message": "Thumbnail regeneration completed",
    "result": {
        "total_processed": 15,
        "success_count": 12,
        "failed_count": 3
    }
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

### **GET /api/user/history**
**Description:** Get unified user history combining sessions, challenges, and dance breakdowns  
**Authentication:** Required  

**Parameters:**
- `page` (query): Page number (default: 1)
- `limit` (query): Items per page (default: 20)
- `activity_type` (query): Filter by activity type - 'session', 'challenge', 'breakdown', or null for all (default: null)

**Response:**
```json
{
  "activities": [
    {
      "_id": "68936a1f93b74bc4f0112219",
      "activityType": "session",
      "activityTitle": "Hip Hop Session",
      "activitySubtitle": "15 min • 120 cal",
      "timestamp": "2025-08-06T14:43:43.280000",
      "previewImage": "https://example.com/thumbnail.jpg",
      "metadata": {
        "duration": 15,
        "calories": 120,
        "style": "Hip Hop",
        "score": 85,
        "level": 2
      }
    },
    {
      "_id": "6893835c1ef74973896e2bf3",
      "activityType": "challenge",
      "activityTitle": "Freestyle Friday Challenge",
      "activitySubtitle": "Score: 92 • 8 min",
      "timestamp": "2025-08-06T16:31:23.000000",
      "previewImage": "https://example.com/challenge-thumb.jpg",
      "metadata": {
        "score": 92,
        "duration": 8,
        "calories": 65,
        "challengeTitle": "Freestyle Friday",
        "challengeType": "freestyle",
        "points": 100
      }
    },
    {
      "_id": "689384f3feb56ff7db9aad0f",
      "activityType": "breakdown",
      "activityTitle": "Dance Breakdown",
      "activitySubtitle": "9 steps • Intermediate",
      "timestamp": "2025-08-06T16:38:11.368000",
      "previewImage": "https://example.com/breakdown-thumb.jpg",
      "metadata": {
        "totalSteps": 9,
        "duration": 30,
        "difficulty": "Intermediate",
        "originalUrl": "https://www.youtube.com/shorts/xMmYwTXrW8g",
        "playableUrl": "https://s3.amazonaws.com/breakdown.mp4"
      }
    }
  ],
  "total": 3,
  "page": 1,
  "limit": 20,
  "hasMore": false,
  "summary": {
    "sessions": 1,
    "challenges": 1,
    "breakdowns": 1,
    "total": 3
  }
}
```

**Activity Types:**
- **`session`**: Dance practice sessions with duration, calories, style, and score
- **`challenge`**: Challenge submissions with score, duration, challenge details, and points
- **`breakdown`**: Dance breakdowns with step count, difficulty, and video URLs

**Frontend Usage:**
- Use `activityType` to show different icons/colors for each activity
- Use `activityTitle` and `activitySubtitle` for display text
- Use `previewImage` for thumbnails/video previews
- Use `metadata` for detailed information specific to each activity type
- Use `summary` to show total counts for each activity type 