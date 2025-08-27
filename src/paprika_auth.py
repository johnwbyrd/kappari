#!/usr/bin/env python3
"""
Paprika 3 authentication implementation
"""

import base64
import sqlite3
import hashlib
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA1
import os
import json
import sys

# Try to import requests, but handle if it's not available
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: requests library not available. Authentication features will be disabled.")
    print("To enable authentication, install with: pip install requests")

class PaprikaAuth:
    def __init__(self, db_path="/home/jbyrd/git/paprika/captures/sqlite/Paprika.sqlite"):
        self.db_path = db_path
        self.base_url = "https://www.paprikaapp.com/api/v2"
        self.license_data = None
        self.signature = None
        
    def decrypt_license_data(self):
        """Decrypt license data from SQLite database"""
        if not os.path.exists(self.db_path):
            raise Exception(f"Database not found: {self.db_path}")
        
        # Connect to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get encrypted purchase data
        cursor.execute("SELECT product_id, data, signature FROM purchases")
        row = cursor.fetchone()
        
        if not row:
            raise Exception("No purchase data found in database")
            
        product_id, encrypted_data, encrypted_signature = row
        
        # Use the confirmed encryption keys
        data_key = "Purchase Data"
        signature_key = "Purchase Signature"
        
        # Decrypt license data
        self.license_data = self._decrypt_data(encrypted_data, data_key)
        if self.license_data.startswith("Decryption failed"):
            raise Exception(f"Failed to decrypt license data: {self.license_data}")
        
        # Decrypt signature
        signature_raw = self._decrypt_data(encrypted_signature, signature_key)
        if signature_raw.startswith("Decryption failed"):
            raise Exception(f"Failed to decrypt signature: {signature_raw}")
            
        # Base64 encode the signature for transmission
        self.signature = base64.b64encode(signature_raw.encode('utf-8')).decode('utf-8')
        
        conn.close()
        return True
    
    def _decrypt_data(self, encrypted_b64, password):
        """Decrypt Paprika encrypted data"""
        try:
            # Decode base64
            encrypted_data = base64.b64decode(encrypted_b64)
            
            # First 32 bytes are the salt
            salt = encrypted_data[:32]
            ciphertext = encrypted_data[32:]
            
            # Use 1000 iterations
            iterations = 1000
            
            # Derive key and IV using PBKDF2
            key_iv = PBKDF2(password.encode('utf-8'), salt, 48, count=iterations, hmac_hash_module=SHA1)
            key = key_iv[:32]  # 256-bit AES key
            iv = key_iv[32:48]  # 128-bit IV
            
            # Decrypt with AES-256-CBC
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted_padded = cipher.decrypt(ciphertext)
            
            # Remove PKCS7 padding
            padding_len = decrypted_padded[-1]
            if 1 <= padding_len <= 16:
                # Verify padding is correct
                padding_bytes = decrypted_padded[-padding_len:]
                if all(b == padding_len for b in padding_bytes):
                    decrypted = decrypted_padded[:-padding_len]
                    result = decrypted.decode('utf-8')
                    return result
            
            return f"Decryption failed: Invalid padding"
            
        except Exception as e:
            return f"Decryption failed: {e}"
    
    def authenticate(self, email, password):
        """Authenticate with Paprika server and get JWT token"""
        if not REQUESTS_AVAILABLE:
            raise Exception("Requests library not available. Cannot perform authentication.")
            
        if not self.license_data or not self.signature:
            raise Exception("License data not decrypted. Call decrypt_license_data() first.")
        
        # Prepare login request
        login_url = f"{self.base_url}/account/login/"
        
        # The license data needs to be sent as JSON
        try:
            license_json = json.loads(self.license_data)
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid license data JSON: {e}")
        
        # Prepare multipart form data
        files = {
            'email': (None, email),
            'password': (None, password),
            'data': (None, self.license_data),
            'signature': (None, self.signature)
        }
        
        headers = {
            'User-Agent': 'Paprika Recipe Manager 3/3.3.1 (Microsoft Windows NT 10.0.26100.0)'
        }
        
        print(f"Attempting to authenticate with email: {email}")
        print(f"License key: {license_json.get('key', 'N/A')}")
        print(f"Product ID: {license_json.get('product_id', 'N/A')}")
        
        try:
            response = requests.post(login_url, files=files, headers=headers, timeout=30)
            
            print(f"Server response: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if 'result' in result and 'token' in result['result']:
                        jwt_token = result['result']['token']
                        print("Authentication successful!")
                        print(f"JWT Token: {jwt_token}")
                        return jwt_token
                    else:
                        print(f"Unexpected response format: {result}")
                        return None
                except json.JSONDecodeError:
                    print(f"Non-JSON response: {response.text}")
                    return None
            else:
                print(f"Authentication failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None
    
    def make_authenticated_request(self, endpoint, jwt_token):
        """Make an authenticated request to Paprika API"""
        if not REQUESTS_AVAILABLE:
            raise Exception("Requests library not available. Cannot make authenticated requests.")
            
        url = f"{self.base_url}/{endpoint}"
        
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'User-Agent': 'Paprika Recipe Manager 3/3.3.1 (Microsoft Windows NT 10.0.26100.0)'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            return response
        except requests.exceptions.RequestException as e:
            print(f"Authenticated request failed: {e}")
            return None

def main():
    # Example usage
    auth = PaprikaAuth()
    
    try:
        # Decrypt license data
        print("Decrypting license data...")
        auth.decrypt_license_data()
        print("License data decrypted successfully!")
        
        # Parse license data to show what we have
        license_json = json.loads(auth.license_data)
        print(f"\nLicense Information:")
        print(f"  Key: {license_json.get('key', 'N/A')}")
        print(f"  Name: {license_json.get('name', 'N/A')}")
        print(f"  Email: {license_json.get('email', 'N/A')}")
        print(f"  Product: {license_json.get('product_id', 'N/A')}")
        print(f"  Purchase Date: {license_json.get('purchase_date', 'N/A')}")
        
        # To actually authenticate, you would need your Paprika account credentials
        # Uncomment and fill in the following lines with your actual credentials:
        # 
        # email = "your_email@example.com"
        # password = "your_password"
        # jwt_token = auth.authenticate(email, password)
        # 
        # if jwt_token:
        #     # Example of making an authenticated request
        #     response = auth.make_authenticated_request("sync/recipes/", jwt_token)
        #     if response and response.status_code == 200:
        #         print("Successfully made authenticated request!")
        #         print(f"Response: {response.json()}")
        #     else:
        #         print("Failed to make authenticated request")
        
        print("\nAuthentication module ready!")
        print("To authenticate, call auth.authenticate(email, password) with your Paprika credentials")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()