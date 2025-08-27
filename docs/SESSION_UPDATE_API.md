# Session Update API Documentation

## Overview

The Session Update API enables Instagram-like editing capabilities for dance sessions. Users can update session metadata both before and after completion, providing a flexible and user-friendly experience.

## Endpoint

### PUT /api/sessions/{session_id}/update

Updates session metadata with smart field restrictions based on session status.

**Authentication:** Required (JWT Bearer Token)

## Request

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | Yes | Session ID to update |

### Request Body

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

### Field Descriptions

| Field | Type | Description | Editable After Completion |
|-------|------|-------------|---------------------------|
| `style` | string | Dance style (e.g., "hip hop", "ballet") | ❌ No |
| `sessionType` | string | Session type (e.g., "freestyle", "choreography") | ❌ No |
| `isPublic` | boolean | Whether session is public | ✅ Yes |
| `sharedToFeed` | boolean | Whether session is shared to feed | ✅ Yes |
| `remixable` | boolean | Whether session can be remixed | ✅ Yes |
| `promptUsed` | string | Dance prompt used for the session | ❌ No |
| `inspirationSessionId` | string | ID of inspiration session | ❌ No |
| `location` | string | Session location | ✅ Yes |
| `highlightText` | string | Main description/caption | ✅ Yes |
| `tags` | array | Session tags | ✅ Yes |

## Response

### Success Response

**Status Code:** 200 OK

```json
{
    "message": "Session updated successfully"
}
```

### Error Responses

**Status Code:** 400 Bad Request
```json
{
    "detail": "Cannot update these fields after completion: style, sessionType"
}
```

**Status Code:** 404 Not Found
```json
{
    "detail": "Session not found or access denied"
}
```

## Field Restrictions

### Always Editable (Instagram-like)
These fields can be updated anytime, even after session completion:
- `highlightText` - Main description/caption
- `tags` - Session tags
- `location` - Session location
- `isPublic` - Public/private setting
- `sharedToFeed` - Feed sharing setting
- `remixable` - Remix permission

### Pre-completion Only
These fields can only be updated before session completion:
- `style` - Dance style
- `sessionType` - Session type
- `promptUsed` - Dance prompt
- `inspirationSessionId` - Inspiration session

### Never Editable
These fields cannot be updated at any time:
- Video-related fields (videoURL, videoFileKey, etc.)
- Session metadata (startTime, endTime, duration, etc.)

## Usage Examples

### Update Before Completion

```bash
curl -X PUT "http://localhost:8000/api/sessions/123456/update" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "style": "hip hop",
    "sessionType": "freestyle",
    "highlightText": "My amazing dance session!",
    "tags": ["dance", "hiphop", "fun"]
  }'
```

### Update After Completion (Instagram-like)

```bash
curl -X PUT "http://localhost:8000/api/sessions/123456/update" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "highlightText": "Updated description after posting! 🎵",
    "tags": ["dance", "hiphop", "fun", "viral"],
    "location": "Updated Location"
  }'
```

### Partial Update

```bash
curl -X PUT "http://localhost:8000/api/sessions/123456/update" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "highlightText": "Just updating the description"
  }'
```

## Error Handling

### Common Error Scenarios

1. **Trying to update restricted fields after completion**
   ```json
   {
     "detail": "Cannot update these fields after completion: style, sessionType"
   }
   ```

2. **Session not found or access denied**
   ```json
   {
     "detail": "Session not found or access denied"
   }
   ```

3. **Invalid inspirationSessionId format**
   ```json
   {
     "detail": "Invalid inspirationSessionId format"
   }
   ```

## Implementation Details

### Database Operations

The API performs the following operations:
1. Validates session ownership
2. Checks session completion status
3. Applies field restrictions based on status
4. Updates only provided fields
5. Updates `updatedAt` timestamp

### Security Features

- **Authentication Required**: JWT token validation
- **Authorization**: Only session owner can update
- **Field Validation**: Type safety and format validation
- **Status Validation**: Smart field restrictions

## Integration

### Frontend Integration

```javascript
// Update session metadata
const updateSession = async (sessionId, updateData) => {
  try {
    const response = await fetch(`/api/sessions/${sessionId}/update`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(updateData)
    });
    
    if (response.ok) {
      return await response.json();
    } else {
      const error = await response.json();
      throw new Error(error.detail);
    }
  } catch (error) {
    console.error('Failed to update session:', error);
    throw error;
  }
};
```

### Mobile App Integration

```dart
// Flutter/Dart example
Future<void> updateSession(String sessionId, Map<String, dynamic> updateData) async {
  try {
    final response = await http.put(
      Uri.parse('$baseUrl/api/sessions/$sessionId/update'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
      body: jsonEncode(updateData),
    );
    
    if (response.statusCode == 200) {
      print('Session updated successfully');
    } else {
      throw Exception('Failed to update session');
    }
  } catch (e) {
    print('Error updating session: $e');
  }
}
```

## Testing

### Test Scenarios

1. **Update before completion** - All fields editable
2. **Update after completion** - Only Instagram-like fields editable
3. **Restricted field updates** - Proper error handling
4. **Partial updates** - Only provided fields updated
5. **Authentication** - Proper authorization checks
6. **Error cases** - Invalid data handling

### Running Tests

```bash
# Run direct logic tests
python scripts/test_session_update_direct.py

# Run HTTP API tests (requires server)
python scripts/test_session_update_api.py
```

## Best Practices

### For Frontend Developers

1. **Check session status** before attempting updates
2. **Handle field restrictions** gracefully in UI
3. **Provide clear feedback** for restricted operations
4. **Use optimistic updates** for better UX
5. **Implement proper error handling**

### For Backend Developers

1. **Validate all inputs** before processing
2. **Use proper error codes** for different scenarios
3. **Log important operations** for debugging
4. **Maintain backward compatibility**
5. **Follow existing code patterns**

## Changelog

### Version 1.0 (Current)
- ✅ Initial implementation
- ✅ Instagram-like editing support
- ✅ Smart field restrictions
- ✅ Comprehensive error handling
- ✅ Full test coverage

## Support

For questions or issues related to the Session Update API:

1. Check the error responses for specific details
2. Review the field restrictions documentation
3. Test with the provided examples
4. Contact the development team for assistance

---

**Last Updated:** August 27, 2025  
**Version:** 1.0  
**Status:** Production Ready ✅ 