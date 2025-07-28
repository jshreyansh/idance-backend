import httpx
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from fastapi import HTTPException
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv

load_dotenv()

# Get Google Client ID from environment variables
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

async def verify_google_token(id_token_str: str) -> Dict[str, Any]:
    """
    Verify Google ID token and return user information
    """
    try:
        # Verify the token
        id_info = id_token.verify_oauth2_token(
            id_token_str, 
            Request(), 
            GOOGLE_CLIENT_ID
        )
        
        # Validate issuer
        if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
            
        return {
            'google_id': id_info['sub'],
            'email': id_info.get('email'),
            'name': id_info.get('name'),
            'picture': id_info.get('picture'),
            'email_verified': id_info.get('email_verified', False),
            'given_name': id_info.get('given_name'),
            'family_name': id_info.get('family_name'),
            'locale': id_info.get('locale')
        }
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")

async def fetch_google_profile_data(access_token: str) -> Optional[Dict[str, Any]]:
    """
    Fetch extended user profile data from Google People API
    """
    try:
        url = "https://people.googleapis.com/v1/people/me"
        params = {
            'personFields': 'names,emailAddresses,photos,birthdays,genders,phoneNumbers,addresses,locales'
        }
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                profile_data = response.json()
                
                # Extract relevant information
                extracted_data = {}
                
                # Birthday
                if 'birthdays' in profile_data and profile_data['birthdays']:
                    for birthday in profile_data['birthdays']:
                        if birthday.get('metadata', {}).get('primary'):
                            date = birthday.get('date', {})
                            if 'year' in date:
                                extracted_data['birth_year'] = date['year']
                            break
                
                # Gender
                if 'genders' in profile_data and profile_data['genders']:
                    for gender in profile_data['genders']:
                        if gender.get('metadata', {}).get('primary'):
                            extracted_data['gender'] = gender.get('value', '').lower()
                            break
                
                # Phone numbers
                if 'phoneNumbers' in profile_data and profile_data['phoneNumbers']:
                    for phone in profile_data['phoneNumbers']:
                        if phone.get('metadata', {}).get('primary'):
                            extracted_data['phone'] = phone.get('value')
                            break
                
                # Address/Location
                if 'addresses' in profile_data and profile_data['addresses']:
                    for address in profile_data['addresses']:
                        if address.get('metadata', {}).get('primary'):
                            extracted_data['location'] = {
                                'city': address.get('city'),
                                'country': address.get('country')
                            }
                            break
                
                return extracted_data
                
    except Exception as e:
        # If profile data fetch fails, don't block the sign-in process
        print(f"Failed to fetch Google profile data: {str(e)}")
        return None
    
    return None 