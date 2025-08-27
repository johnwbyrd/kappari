#!/usr/bin/env python3
"""
Example script showing how to use the Paprika authentication module
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from paprika_auth import PaprikaAuth
    import json
except ImportError as e:
    print(f"Missing required library: {e}")
    print("Please install required dependencies:")
    print("  pip install requests pycryptodome")
    sys.exit(1)

def main():
    print("Paprika 3 Authentication Example")
    print("=" * 40)
    
    # Initialize the authentication module
    auth = PaprikaAuth()
    
    try:
        # Decrypt license data from local database
        print("Step 1: Decrypting license data from local database...")
        auth.decrypt_license_data()
        print("License data decrypted successfully")
        
        # Show license information
        license_json = json.loads(auth.license_data)
        print(f"\nLicense Information:")
        print(f"  Key: {license_json.get('key', 'N/A')}")
        print(f"  Name: {license_json.get('name', 'N/A')}")
        print(f"  Email: {license_json.get('email', 'N/A')}")
        print(f"  Product: {license_json.get('product_id', 'N/A')}")
        
        print("\nStep 2: Authenticate with Paprika server")
        print("To authenticate, you need your Paprika account credentials:")
        print("  - Email address")
        print("  - Password")
        print("\nExample usage:")
        print("  email = 'your_email@example.com'")
        print("  password = 'your_password'")
        print("  jwt_token = auth.authenticate(email, password)")
        print("\nNote: This requires a valid Paprika account with the license above.")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
