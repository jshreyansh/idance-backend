# 🚀 Production Deployment Guide

## **Overview**

This guide explains how to deploy your iDance backend to EC2 with proper environment separation between local development and production.

## **🏗️ Environment Architecture**

### **Collection Separation**
- **Local Development**: Uses base collection names (`users`, `challenges`, `dance_sessions`)
- **EC2 Production**: Uses production collections (`users_prod`, `challenges_prod`, `dance_sessions_prod`)
- **Testing**: Uses test collections (`users_test`, `challenges_test`, `dance_sessions_test`)

### **Automatic Switching**
The system automatically switches collections based on the `ENVIRONMENT` variable:

```python
# When ENVIRONMENT=development
db['users'] → uses "users" collection

# When ENVIRONMENT=production  
db['users'] → uses "users_prod" collection

# When ENVIRONMENT=test
db['users'] → uses "users_test" collection
```

## **🔧 Local Development Setup**

### **1. Create Local .env File**
```bash
# Create .env file in your project root
touch .env
```

### **2. Add Environment Configuration**
```bash
# Add to your .env file
ENVIRONMENT=development

# Other configurations...
JWT_SECRET=your-local-jwt-secret
GOOGLE_CLIENT_ID=your-google-client-id
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
# ... rest of your config
```

### **3. Start Local Server**
```bash
# Activate virtual environment
source venv/bin/activate

# Start server (will use development collections)
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Result**: Server will use `users`, `challenges`, `dance_sessions` collections

## **☁️ EC2 Production Setup**

### **1. SSH into EC2**
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### **2. Clone/Setup Project**
```bash
# Clone your repository
git clone https://github.com/your-repo/idance-backend.git
cd idance-backend

# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### **3. Create Production .env File**
```bash
# Create production environment file
nano .env
```

### **4. Add Production Configuration**
```bash
# Production environment configuration
ENVIRONMENT=production

# Production JWT secret (use a strong, unique secret)
JWT_SECRET=your-super-strong-production-jwt-secret-here

# Google OAuth (same as development)
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_ID_WEB=your-google-client-id-web.apps.googleusercontent.com

# MongoDB (same database, different collections)
MONGO_URL=mongodb+srv://dbshreyansh:dbshreyansh@cluster0.syqn1pb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
DATABASE_NAME=idance

# AWS S3 (production bucket)
AWS_ACCESS_KEY_ID=your-production-aws-key
AWS_SECRET_ACCESS_KEY=your-production-aws-secret
AWS_REGION=ap-south-1
S3_BUCKET_NAME=idanceshreyansh
S3_BUCKET_URL=https://idanceshreyansh.s3.ap-south-1.amazonaws.com

# Production API configuration
API_HOST=0.0.0.0
API_PORT=8000
```

### **5. Start Production Server**
```bash
# Activate virtual environment
source venv/bin/activate

# Start production server
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

**Result**: Server will use `users_prod`, `challenges_prod`, `dance_sessions_prod` collections

## **📊 Data Migration Status**

### **✅ Migration Already Complete**

The data migration has already been completed by the setup script:

```bash
# This was already run and completed successfully
python scripts/setup_database_environments.py
```

### **Current State**
- **Development Collections**: `users` (41 docs), `challenges` (9 docs), etc.
- **Production Collections**: `users_prod` (41 docs), `challenges_prod` (9 docs), etc.
- **Test Collections**: `users_test` (0 docs), `challenges_test` (0 docs), etc.

### **No Additional Migration Needed**
Your production data is already migrated and ready to use!

## **🔍 Verification Commands**

### **Check Current Environment**
```bash
# The server will show which environment it's using
✅ Connected to MongoDB (Environment: development)  # or production
```

### **Verify Collection Usage**
```bash
# Check which collections are being used
# Development: users, challenges, dance_sessions
# Production: users_prod, challenges_prod, dance_sessions_prod
```

## **🔄 Environment Switching Examples**

### **Local Development**
```bash
# .env file
ENVIRONMENT=development

# Server output
✅ Connected to MongoDB (Environment: development)

# Collections used: users, challenges, dance_sessions
```

### **EC2 Production**
```bash
# .env file  
ENVIRONMENT=production

# Server output
✅ Connected to MongoDB (Environment: production)

# Collections used: users_prod, challenges_prod, dance_sessions_prod
```

### **Testing**
```bash
# .env file
ENVIRONMENT=test

# Server output
✅ Connected to MongoDB (Environment: test)

# Collections used: users_test, challenges_test, dance_sessions_test
```

## **🚨 Important Notes**

### **1. Environment Variable is the Switch**
- **No code changes needed** - just change `ENVIRONMENT` in `.env`
- **Automatic collection switching** based on environment
- **Same database, different collections**

### **2. Data Isolation**
- **Local development**: Uses development collections
- **EC2 production**: Uses production collections
- **No data conflicts** between environments

### **3. Security**
- **Different JWT secrets** for development vs production
- **Same MongoDB database** but separate collections
- **Production data is protected** in `_prod` collections

### **4. No Migration Needed**
- **Data already migrated** by setup script
- **Production collections ready** to use
- **Just set ENVIRONMENT=production** on EC2

## **🎯 Quick Deployment Checklist**

### **Local Development**
- [ ] Set `ENVIRONMENT=development` in `.env`
- [ ] Start server with `uvicorn api.main:app --reload`
- [ ] Verify: "Connected to MongoDB (Environment: development)"

### **EC2 Production**
- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Use strong JWT secret
- [ ] Start server with `uvicorn api.main:app --host 0.0.0.0 --port 8000`
- [ ] Verify: "Connected to MongoDB (Environment: production)"

## **🔧 Troubleshooting**

### **Wrong Collections Being Used**
```bash
# Check environment variable
echo $ENVIRONMENT

# Check .env file
cat .env | grep ENVIRONMENT
```

### **Server Not Starting**
```bash
# Check if .env file exists
ls -la .env

# Check environment variable is set
python -c "import os; print(os.getenv('ENVIRONMENT', 'not set'))"
```

### **Data Not Appearing**
```bash
# Verify you're using the right environment
# Development: check 'users' collection
# Production: check 'users_prod' collection
```

## **📈 Benefits**

1. **✅ Automatic Separation**: No manual switching needed
2. **✅ Data Safety**: Production data isolated in `_prod` collections
3. **✅ Easy Testing**: Clean test environment with `_test` collections
4. **✅ No Migration**: Data already migrated and ready
5. **✅ Simple Configuration**: Just change one environment variable

Your setup is complete and ready for production deployment! 🎉 