# 🔧 Username System Fix

## 🚨 Problem

The application was experiencing a MongoDB duplicate key error when users signed up via Google OAuth:

```
E11000 duplicate key error collection: idance.users index: profile.username_1 dup key: { profile.username: null }
```

**Root Cause:**
- There was a unique index on `profile.username` field
- When users signed up via Google, the username was set to `None` (null)
- MongoDB unique indexes treat multiple `null` values as duplicates
- This caused the error when multiple users tried to sign up

## ✅ Solution Implemented

### 1. **Automatic Username Generation**

Created a `generate_unique_username()` function that:
- Takes the user's name from Google profile or email
- Cleans the name (removes special characters, converts to lowercase)
- Generates a unique username by appending numbers if needed
- Falls back to random username if needed

**Example:**
- User name: "Shreyansh Jaiswal" → `shreyanshjaiswal`
- If taken: `shreyanshjaiswal1`, `shreyanshjaiswal2`, etc.
- Fallback: `userabc123` (random)

### 2. **Updated Authentication Services**

**Google Sign-In (`/auth/google`):**
- Now automatically generates unique username from Google profile name
- No longer sets username to `None`
- Includes extended profile data (gender, birth year, phone, location)

**Email Sign-Up (`/auth/signup`):**
- Generates username from email address (part before @)
- Creates complete profile structure

### 3. **Database Indexes**

Added proper unique indexes:
- `profile.username` - Unique, sparse (allows null values)
- `auth.email` - Unique, sparse
- `auth.providerId` - Non-unique, sparse

### 4. **Data Migration**

Created scripts to fix existing users:
- `scripts/fix_null_usernames.py` - Fixes existing users with null usernames
- `scripts/create_production_indexes.py` - Creates indexes for production

## 🔄 How It Works Now

### For New Users:

1. **Google Sign-In:**
   ```python
   # User signs in with Google
   base_name = google_user_info.get('name', 'user')  # "Shreyansh Jaiswal"
   username = await generate_unique_username(db, users_collection, base_name)
   # Result: "shreyanshjaiswal" or "shreyanshjaiswal1" if taken
   ```

2. **Email Sign-Up:**
   ```python
   # User signs up with email
   email_username = data.email.split('@')[0]  # "john.doe" from "john.doe@gmail.com"
   username = await generate_unique_username(db, users_collection, email_username)
   # Result: "johndoe" or "johndoe1" if taken
   ```

### Username Generation Logic:

```python
def generate_unique_username(base_name):
    # 1. Clean the name
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', base_name.lower())
    
    # 2. Try clean name first
    username = clean_name
    
    # 3. If taken, append numbers
    counter = 1
    while username_exists(username):
        username = f"{clean_name}{counter}"
        counter += 1
    
    # 4. Fallback to random if needed
    if counter > 1000:
        username = f"user{random_suffix}"
    
    return username
```

## 📊 Data Structure

**User Document:**
```json
{
    "_id": "ObjectId",
    "auth": {
        "provider": "google|email",
        "providerId": "google_id",
        "email": "user@example.com",
        "emailVerified": true
    },
    "profile": {
        "username": "shreyanshjaiswal",  // ✅ Always unique, never null
        "displayName": "Shreyansh Jaiswal",
        "avatarUrl": "https://...",
        "gender": "male",
        "birthYear": 1999,
        "location": {...}
    },
    "createdAt": "2025-08-19T06:22:38.203Z",
    "updatedAt": "2025-08-19T06:22:38.203Z"
}
```

## 🛠️ Scripts Created

### 1. `scripts/fix_null_usernames.py`
- Finds users with null usernames
- Generates unique usernames for them
- Updates database records

**Usage:**
```bash
# Fix development environment
python scripts/fix_null_usernames.py

# Fix production environment
ENVIRONMENT=production python scripts/fix_null_usernames.py
```

### 2. `scripts/create_production_indexes.py`
- Creates unique indexes for production environment
- Handles index creation errors gracefully

**Usage:**
```bash
python scripts/create_production_indexes.py
```

## 🔒 Frontend Integration

### What the Frontend Should Send:

**Google Sign-In:**
```json
{
    "idToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "accessToken": "ya29.a0AfH6SMC..."
}
```

**Email Sign-Up:**
```json
{
    "email": "user@example.com",
    "password": "password123"
}
```

### What the Frontend Receives:

```json
{
    "message": "Google sign-in successful",
    "access_token": "jwt_token",
    "token_type": "bearer",
    "user_id": "user_id",
    "user": {
        "email": "user@gmail.com",
        "name": "Shreyansh Jaiswal",
        "picture": "https://...",
        "email_verified": true
    }
}
```

## 🎯 Benefits

1. **No More Duplicate Key Errors** - Usernames are always unique
2. **Automatic Username Generation** - No manual username input required
3. **Consistent Data Structure** - All users have complete profiles
4. **Backward Compatibility** - Existing users are automatically fixed
5. **Scalable** - Handles millions of users with unique usernames

## 🚀 Next Steps

1. **Frontend Updates:**
   - Remove username input field from sign-up forms
   - Display auto-generated username in profile
   - Allow users to change username later if needed

2. **Username Change Feature:**
   - Add API endpoint to allow users to change their username
   - Validate uniqueness before allowing changes
   - Update all references to old username

3. **Username Validation:**
   - Add validation for username format (length, characters)
   - Reserve certain usernames (admin, support, etc.)
   - Add username availability check endpoint

## 📝 Notes

- **Sparse Indexes:** Used sparse indexes to allow null values in other fields while maintaining uniqueness for non-null values
- **Fallback Strategy:** Multiple fallback strategies ensure username generation never fails
- **Performance:** Username generation is fast and efficient with database queries
- **Security:** Usernames are sanitized to prevent injection attacks 