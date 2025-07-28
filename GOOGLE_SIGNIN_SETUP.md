# Google Sign-In Setup Guide

This guide explains how to set up and use the Google Sign-In feature with your iDance backend API.

## 🚀 Quick Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in your project root (copy from `env_example`):

```bash
# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-here-change-in-production

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com

# MongoDB Configuration (if needed)
MONGO_URL=mongodb://localhost:27017
DATABASE_NAME=idance
```

### 3. Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google+ API and People API
4. Go to "Credentials" → "Create Credentials" → "OAuth client ID"
5. Configure OAuth consent screen if prompted
6. For application type, choose "Web application"
7. Add authorized redirect URIs (for your frontend)
8. Copy the **Client ID** to your `.env` file

### 4. Test Configuration

```bash
curl http://localhost:8000/auth/google/test
```

Should return configuration status.

## 📱 Client-Side Integration

### Required Scopes for Extended Data

Update your client-side Google Auth configuration to include these scopes:

```typescript
scopes: [
  'openid',
  'profile', 
  'email',
  'https://www.googleapis.com/auth/user.birthday.read',
  'https://www.googleapis.com/auth/user.gender.read',
  'https://www.googleapis.com/auth/user.phonenumbers.read',
]
```

### API Call Example

```typescript
// After successful Google Sign-In on client
const response = await fetch('http://your-api-domain/auth/google', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    idToken: googleResponse.idToken,
    accessToken: googleResponse.accessToken,
  }),
});

const data = await response.json();
// Use data.access_token for subsequent API calls
```

## 🔧 API Endpoints

### `POST /auth/google`

Sign in or sign up using Google OAuth tokens.

**Request Body:**
```json
{
  "idToken": "google_id_token_here",
  "accessToken": "google_access_token_here"
}
```

**Response:**
```json
{
  "message": "Google sign-in successful",
  "access_token": "your_jwt_token",
  "token_type": "bearer",
  "user_id": "user_id_here",
  "user": {
    "email": "user@example.com",
    "name": "John Doe",
    "picture": "https://profile-picture-url",
    "email_verified": true
  }
}
```

### `GET /auth/google/test`

Test endpoint to verify Google OAuth configuration.

**Response:**
```json
{
  "status": "Google OAuth configuration check",
  "google_client_id_configured": true,
  "jwt_secret_configured": true,
  "endpoints_available": [...]
}
```

## 📊 User Data Handling

### What Data is Collected

**From ID Token (Basic):**
- Google ID
- Email address
- Full name
- Profile picture
- Email verification status

**From People API (Extended - if permissions granted):**
- Birthday/Birth year
- Gender
- Phone number
- Address/Location

### User Document Structure

```json
{
  "_id": "mongodb_object_id",
  "auth": {
    "provider": "google",
    "providerId": "google_user_id",
    "email": "user@example.com",
    "phone": "+1234567890",
    "passwordHash": null,
    "emailVerified": true,
    "phoneVerified": true
  },
  "profile": {
    "username": null,
    "displayName": "John Doe",
    "avatarUrl": "https://profile-picture-url",
    "bio": null,
    "gender": "male",
    "birthYear": 1990,
    "location": {
      "city": "San Francisco",
      "country": "USA"
    }
  },
  "createdAt": "2024-01-01T00:00:00.000Z",
  "lastLoginAt": "2024-01-01T00:00:00.000Z",
  "updatedAt": "2024-01-01T00:00:00.000Z"
}
```

## 🔐 Security Features

- **Token Verification**: All Google ID tokens are verified against Google's servers
- **Secure JWT**: Uses your custom JWT secret for session tokens
- **Email Matching**: Links Google accounts to existing email accounts if same email
- **Error Handling**: Comprehensive error handling for invalid tokens
- **Privacy Compliant**: Extended data fetching fails gracefully if permissions denied

## 🚨 Error Handling

### Common Errors:

1. **Invalid Google Token (401)**
   ```json
   {"detail": "Invalid Google token: Wrong issuer."}
   ```

2. **Missing Configuration (500)**
   ```json
   {"detail": "Internal server error during Google sign-in"}
   ```

3. **Network Issues**
   - People API call failures are handled gracefully
   - User can still sign in with basic profile data

## 🧪 Testing

### Manual Testing

1. Use Google OAuth playground to get tokens
2. Test with curl:

```bash
curl -X POST http://localhost:8000/auth/google \
  -H "Content-Type: application/json" \
  -d '{
    "idToken": "your_google_id_token",
    "accessToken": "your_google_access_token"
  }'
```

### Integration Testing

1. Check configuration: `GET /auth/google/test`
2. Test sign-in flow with real Google tokens
3. Verify JWT token works with protected endpoints
4. Test user profile data population

## 🔄 Migration Notes

- Existing email users can sign in with Google using same email
- Their account will be converted to Google provider
- All existing data is preserved
- JWT tokens remain compatible with existing system

## 📝 Next Steps

1. Set up environment variables
2. Configure Google Cloud Console
3. Update client-side scopes
4. Test the implementation
5. Deploy to production

That's it! Your Google Sign-In integration is now complete and ready to use. 🎉 