# 🗄️ Database Environment Setup Guide

## **Overview**

This guide helps you set up separate database collections for different environments (development, test, production) to keep your data organized and prevent conflicts.

## **🏗️ Architecture**

### **Collection Naming Convention**
- **Development**: `users`, `challenges`, `dance_sessions` (base names)
- **Test**: `users_test`, `challenges_test`, `dance_sessions_test`
- **Production**: `users_prod`, `challenges_prod`, `dance_sessions_prod`

### **Environment Configuration**
Set the `ENVIRONMENT` variable in your `.env` file:
```bash
# For development (default)
ENVIRONMENT=development

# For testing
ENVIRONMENT=test

# For production
ENVIRONMENT=production
```

## **🚀 Quick Setup**

### **Step 1: Set Environment Variable**
```bash
# Add to your .env file
ENVIRONMENT=development
```

### **Step 2: Run Database Setup**
```bash
# Activate virtual environment
source venv/bin/activate

# Run the setup script
python scripts/setup_database_environments.py
```

### **Step 3: Update Service Files (Optional)**
```bash
# Update collection references in service files
python scripts/update_collection_references.py
```

## **📋 What the Setup Script Does**

1. **Lists Current Collections**: Shows all existing collections and document counts
2. **Creates Production Collections**: Migrates existing data to `_prod` collections
3. **Creates Test Collections**: Creates empty `_test` collections
4. **Creates Development Collections**: Migrates data to base collection names
5. **Creates Indexes**: Sets up optimized indexes for all environments
6. **Provides Summary**: Shows final collection structure

## **🔧 Manual Setup (Alternative)**

If you prefer to set up manually:

### **1. Create Collections**
```javascript
// In MongoDB shell or Compass
use idance

// Create production collections
db.users_prod.insertOne({__temp__: true})
db.challenges_prod.insertOne({__temp__: true})
db.dance_sessions_prod.insertOne({__temp__: true})
// ... repeat for all collections

// Create test collections
db.users_test.insertOne({__temp__: true})
db.challenges_test.insertOne({__temp__: true})
db.dance_sessions_test.insertOne({__temp__: true})
// ... repeat for all collections

// Clean up temp documents
db.users_prod.deleteOne({__temp__: true})
db.challenges_prod.deleteOne({__temp__: true})
// ... repeat for all collections
```

### **2. Migrate Data**
```javascript
// Copy data from existing collections to production
db.users.find().forEach(function(doc) {
    db.users_prod.insertOne(doc);
});

db.challenges.find().forEach(function(doc) {
    db.challenges_prod.insertOne(doc);
});

// ... repeat for all collections
```

### **3. Create Indexes**
```javascript
// Users indexes
db.users_prod.createIndex({"auth.email": 1}, {unique: true, sparse: true})
db.users_test.createIndex({"auth.email": 1}, {unique: true, sparse: true})

// Challenges indexes
db.challenges_prod.createIndex({"isActive": 1, "startTime": 1, "endTime": 1})
db.challenges_test.createIndex({"isActive": 1, "startTime": 1, "endTime": 1})

// ... repeat for all collections
```

## **📊 Collection Structure**

### **Core Collections**
- `users` - User accounts and profiles
- `user_stats` - User statistics and achievements
- `user_badges` - User badges and rewards

### **Challenge System**
- `challenges` - Challenge definitions
- `challenge_submissions` - User challenge submissions
- `leaderboards` - Challenge leaderboards

### **Session System**
- `dance_sessions` - Dance practice sessions
- `session_likes` - Session likes and engagement

### **AI & Analysis**
- `dance_breakdowns` - Dance video breakdowns
- `pose_analysis` - Pose analysis results

### **Feed System**
- `feed_items` - Social feed items

### **Background Jobs**
- `background_jobs` - Background job tracking
- `job_queue` - Job queue management

## **🔄 Environment Switching**

### **Development**
```bash
ENVIRONMENT=development
# Uses: users, challenges, dance_sessions, etc.
```

### **Testing**
```bash
ENVIRONMENT=test
# Uses: users_test, challenges_test, dance_sessions_test, etc.
```

### **Production**
```bash
ENVIRONMENT=production
# Uses: users_prod, challenges_prod, dance_sessions_prod, etc.
```

## **🧪 Testing Different Environments**

### **Test Environment Setup**
```bash
# Set environment to test
export ENVIRONMENT=test

# Start server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Test with clean data
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123"}'
```

### **Production Environment Setup**
```bash
# Set environment to production
export ENVIRONMENT=production

# Start server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Test with production data
curl -X GET http://localhost:8000/api/users/profile \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## **🔍 Monitoring and Maintenance**

### **Check Collection Status**
```javascript
// In MongoDB shell
use idance

// List all collections
show collections

// Check document counts
db.users_prod.countDocuments()
db.users_test.countDocuments()
db.users.countDocuments()
```

### **Backup Strategy**
```bash
# Backup production collections
mongodump --uri="mongodb+srv://..." --collection=users_prod --collection=challenges_prod

# Backup test collections
mongodump --uri="mongodb+srv://..." --collection=users_test --collection=challenges_test
```

## **⚠️ Important Notes**

1. **Environment Variable**: Always set `ENVIRONMENT` before starting the server
2. **Data Isolation**: Each environment has completely separate data
3. **Indexes**: All environments have the same indexes for consistency
4. **Backup**: Regularly backup production collections
5. **Testing**: Use test environment for automated tests

## **🚨 Troubleshooting**

### **Common Issues**

1. **Wrong Environment**: Check `ENVIRONMENT` variable in `.env`
2. **Missing Collections**: Run setup script again
3. **Index Errors**: Recreate indexes manually
4. **Connection Issues**: Verify MongoDB connection string

### **Reset Environment**
```bash
# Delete and recreate collections
python scripts/setup_database_environments.py
```

## **📈 Benefits**

1. **Data Isolation**: No more test data in production
2. **Safe Testing**: Test with real data structure
3. **Easy Cleanup**: Reset test environment anytime
4. **Production Safety**: Production data is protected
5. **Development Flexibility**: Work with sample data

## **🎯 Next Steps**

1. ✅ Set up environment structure
2. ✅ Migrate existing data
3. ✅ Update service files
4. ✅ Test all environments
5. ✅ Deploy to production with `ENVIRONMENT=production` 