# 🔥 Heatmap API Update: Total Activities

## 🎯 Objective

Update the heatmap API to show **total activities** (sessions + challenges + breakdowns) instead of just sessions, providing a more comprehensive view of user engagement.

## 🔄 Changes Made

### 1. **Updated Response Model**

**Before:**
```python
class HeatmapResponse(BaseModel):
    date: str
    sessionsCount: int  # Only sessions
    isActive: bool
    caloriesBurned: int = 0
```

**After:**
```python
class HeatmapResponse(BaseModel):
    date: str
    activitiesCount: int  # Total activities (sessions + challenges + breakdowns)
    isActive: bool
    caloriesBurned: int = 0
```

### 2. **Enhanced API Logic**

**Added Dance Breakdowns Tracking:**
```python
# Query dance breakdowns in the date range
dance_breakdowns = await db[dance_breakdowns_collection].find({
    "userId": ObjectId(user_id),
    "success": True,
    "createdAt": {
        "$gte": datetime.combine(start_date, datetime.min.time()),
        "$lt": datetime.combine(today + timedelta(days=1), datetime.min.time())
    }
}).to_list(1000)
```

**Updated Activity Counting:**
```python
# Calculate total activities count per day (sessions + challenges + breakdowns)
activities_count_per_day = {}

# Count regular sessions
for session in sessions:
    session_date = session['startTime'].date().strftime('%Y-%m-%d')
    activities_count_per_day[session_date] = activities_count_per_day.get(session_date, 0) + 1

# Count challenge submissions
for submission in challenge_submissions:
    submitted_at = submission.get('timestamps', {}).get('submittedAt')
    if submitted_at:
        submission_date = submitted_at.date().strftime('%Y-%m-%d')
        activities_count_per_day[submission_date] = activities_count_per_day.get(submission_date, 0) + 1

# Count dance breakdowns
for breakdown in dance_breakdowns:
    breakdown_date = breakdown['createdAt'].date().strftime('%Y-%m-%d')
    activities_count_per_day[breakdown_date] = activities_count_per_day.get(breakdown_date, 0) + 1
```

### 3. **Updated API Documentation**

**Endpoint:** `GET /api/stats/heatmap`

**Response:**
```json
[
    {
        "date": "2025-01-25",
        "activitiesCount": 5,  // Total activities (sessions + challenges + breakdowns)
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

## 📊 Data Sources

### **Sessions** (`dance_sessions` collection)
- **Date Field:** `startTime`
- **Filter:** `status: "completed"`
- **Calories:** ✅ Included in `caloriesBurned`

### **Challenges** (`challenge_submissions` collection)
- **Date Field:** `timestamps.submittedAt`
- **Filter:** All submissions
- **Calories:** ❌ Not tracked

### **Dance Breakdowns** (`dance_breakdowns` collection)
- **Date Field:** `createdAt`
- **Filter:** `success: true`
- **Calories:** ❌ Not tracked

## 🧪 Testing Results

**Test Data:**
- **Sessions:** 2
- **Challenges:** 1  
- **Breakdowns:** 16
- **Total Activities:** 19

**Daily Breakdown:**
- 2025-08-13: 0 activities
- 2025-08-14: 0 activities
- 2025-08-15: 0 activities
- 2025-08-16: 1 activities
- 2025-08-17: 1 activities
- 2025-08-18: 17 activities
- 2025-08-19: 0 activities

## 🎯 Benefits

1. **Comprehensive Activity View** - Shows all user engagement types
2. **Better User Experience** - Users see their total activity, not just sessions
3. **Accurate Engagement Metrics** - Reflects true user activity across all features
4. **Consistent with Stats** - Matches the `totalActivities` field in user stats

## 🔒 Frontend Integration

### **Before (Old Response):**
```javascript
// Frontend was expecting sessionsCount
const sessionsCount = response.sessionsCount;
```

### **After (New Response):**
```javascript
// Frontend should now use activitiesCount
const activitiesCount = response.activitiesCount;
```

### **Migration Required:**
- Update frontend to use `activitiesCount` instead of `sessionsCount`
- Update any heatmap visualization to reflect total activities
- Consider updating tooltips/labels to say "Activities" instead of "Sessions"

## 📈 Impact

### **User Engagement Visibility:**
- Users now see their complete activity across all features
- Heatmap reflects true engagement (not just dance sessions)
- Better motivation as all activities contribute to the visual

### **Data Accuracy:**
- More accurate representation of user activity
- Consistent with other stats endpoints
- Better analytics for understanding user behavior

## 🚀 Next Steps

1. **Frontend Updates:**
   - Update heatmap component to use `activitiesCount`
   - Update labels and tooltips
   - Test with real user data

2. **Analytics:**
   - Monitor heatmap usage patterns
   - Track user engagement improvements
   - Consider adding activity type breakdown in tooltips

3. **Future Enhancements:**
   - Add activity type filtering (show only sessions, only challenges, etc.)
   - Add activity type breakdown in hover tooltips
   - Consider different colors for different activity types 