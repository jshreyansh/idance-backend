#!/usr/bin/env python3
"""
Script to help update API documentation when new endpoints are added
"""

import os
import re
from datetime import datetime

def update_api_documentation():
    """Update the API documentation with current date"""
    
    # Read the current documentation
    with open('API_DOCUMENTATION.md', 'r') as f:
        content = f.read()
    
    # Update the last updated date
    current_date = datetime.now().strftime("%B %d, %Y")
    
    # Replace the last updated date
    content = re.sub(
        r'\*\*Last Updated:\*\* .*',
        f'**Last Updated:** {current_date}',
        content
    )
    
    # Write back the updated content
    with open('API_DOCUMENTATION.md', 'w') as f:
        f.write(content)
    
    print(f"✅ API documentation updated with current date: {current_date}")

def add_new_endpoint_section():
    """Template for adding new endpoint sections"""
    
    template = """
## 🆕 New Endpoint Section

### **METHOD /api/new-endpoint**
**Description:** Brief description of what this endpoint does  
**Authentication:** Required/Not required  

**Request Body:**
```json
{
    "field1": "value1",
    "field2": "value2"
}
```

**Response:**
```json
{
    "message": "Success response",
    "data": {
        "id": "example_id",
        "status": "success"
    }
}
```

**Status Codes:**
- `200` - Success
- `400` - Bad Request
- `401` - Unauthorized
"""
    
    print("📝 Template for new endpoint section:")
    print(template)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "update":
            update_api_documentation()
        elif sys.argv[1] == "template":
            add_new_endpoint_section()
        else:
            print("Usage:")
            print("  python scripts/update_api_docs.py update    # Update last updated date")
            print("  python scripts/update_api_docs.py template  # Show template for new endpoint")
    else:
        print("API Documentation Helper")
        print("=======================")
        print("1. To update the last updated date:")
        print("   python scripts/update_api_docs.py update")
        print()
        print("2. To see template for new endpoint:")
        print("   python scripts/update_api_docs.py template")
        print()
        print("3. Manual steps for adding new endpoints:")
        print("   - Add the new endpoint section to API_DOCUMENTATION.md")
        print("   - Update the table of contents if needed")
        print("   - Update the last updated date")
        print("   - Commit the changes") 