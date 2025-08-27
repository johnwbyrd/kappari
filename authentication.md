# Paprika Authentication Flow Documentation

## Overview

Paprika uses a dual-layer authentication system combining:
1. **License validation** - Cryptographic signature verification using RSA
2. **Server authentication** - JWT token-based API authentication

## Complete Authentication Flow

### Step 1: License Data Collection

The client must have a valid Paprika license with these components:

#### License Data Structure (GClass28)
```json
{
    "data": {
        "key": "LICENSE-KEY-HERE",  // License key
        "name": "USER NAME HERE",                              // Customer name  
        "email": "user@example.com",                   // Customer email
        "product": "paprika3",                            // Product identifier
        "purchase_date": "2017-08-15T00:00:00.0000000Z",  // Purchase timestamp
        "expired": false,                                 // Expiration status
        "refunded": false,                               // Refund status
        "device": "DEVICE-ID-HERE",                      // Device identifier
        "version": 1                                     // License version
    },
    "signature": "BASE64-RSA-SIGNATURE"                   // Cryptographic signature
}
```

#### Device ID Generation on Windows
Device ID is generated using Windows registry:
1. Check `HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Cryptography\MachineGuid`
2. Fallback to `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Device`  
3. If neither exists, generate new GUID and store in registry

### Step 2: License Validation

Before authentication, the client validates the license:

#### RSA Signature Verification
```csharp
// Load Paprika's public key (embedded in app)
RsaKeyParameters publicKey = PublicKeyFactory.CreateKey(publicKeyBytes);

// Verify signature using SHA256withRSA
ISigner signer = SignerUtilities.GetSigner("SHA256withRSA");
signer.Init(false, publicKey);
signer.BlockUpdate(Encoding.UTF8.GetBytes(licenseDataJson), 0, dataBytes.Length);
bool isValid = signer.VerifySignature(Convert.FromBase64String(signature));
```

#### Validation Checks
1. **Signature verification** - RSA signature must be valid
2. **Product match** - Must be for "paprika3" 
3. **Device match** - Device ID must match current machine
4. **Status checks** - Not expired or refunded
5. **License format** - Must parse as valid JSON

### Step 3: Server Authentication

With valid license, client performs server login:

#### Login API Call
```http
POST /api/v2/account/login/
Content-Type: multipart/form-data

--boundary
Content-Disposition: form-data; name="email"
user@example.com

--boundary  
Content-Disposition: form-data; name="password"
user_password_here

--boundary
Content-Disposition: form-data; name="data"
{license_data_json}

--boundary
Content-Disposition: form-data; name="signature" 
{base64_signature}
```

#### Server Response
```json
{
    "result": {
        "token": "JWT-TOKEN-HERE"
    }
}
```

### Step 4: JWT Token Usage

The returned JWT token is used for all subsequent API calls:

```http
Authorization: Bearer JWT-TOKEN-HERE
```

#### JWT Token Structure
Based on captured tokens, structure appears to be:
```json
{
    "alg": "HS256",
    "typ": "JWT"
}
{
    "iat": 1756246406,           // Issued at timestamp
    "email": "user@example.com" // User email
}
```

## Implementation Details

### API Endpoints

#### Login Endpoint
- **URL**: `POST /api/v2/account/login/`
- **Content-Type**: `multipart/form-data`
- **Fields**:
  - `email` - User email address
  - `password` - User password  
  - `data` - License data JSON
  - `signature` - RSA signature of license data

#### Sync Endpoints
All sync operations require JWT authentication:
- `GET /api/v2/sync/recipes/` - Download recipes
- `POST /api/v2/sync/recipes/` - Upload recipes
- `POST /api/v2/sync/notify/` - Trigger sync notification

### License Storage

Licenses are stored in local SQLite database in `purchases` table:
```sql
CREATE TABLE purchases (
    id INTEGER PRIMARY KEY,
    product TEXT,    -- "paprika3"
    data TEXT,       -- JSON license data
    signature TEXT,  -- Base64 RSA signature
    verified INTEGER -- Last verification timestamp
);
```

### Authentication State Management

The client manages authentication through `GClass24`:

#### Login Process
1. **License retrieval** - Load from database
2. **License validation** - Verify signature and device
3. **Server login** - POST to login endpoint
4. **Token storage** - Store JWT in encrypted settings
5. **API setup** - Configure HTTP client with Bearer token

#### Session Management
- JWT tokens appear to have long expiration (hours/days)
- Client automatically refreshes license validation daily
- WebSocket connection established for real-time sync notifications

## Security Considerations

### License Protection
- **RSA signatures** prevent license tampering
- **Device binding** prevents license sharing
- **Product specificity** prevents cross-app usage

### Network Security
- **HTTPS only** - All API communication encrypted
- **JWT tokens** - Stateless authentication
- **Signature validation** - Server verifies license signatures

### Attack Surface
- **License extraction** - Possible from database/memory
- **Token interception** - Network captures could expose JWT
- **Device spoofing** - Registry manipulation could bypass device checks

## Potential Implementation

For clean-room implementation, you would need:

1. **Valid license** with matching signature (cannot be generated without Paprika's private key)
2. **Device ID** matching the license
3. **Account credentials** for the licensed user
4. **HTTP client** capable of multipart form uploads
5. **JWT handling** for subsequent API calls

The cryptographic signature verification means you cannot create arbitrary licenses - you must use legitimate purchase data from the Paprika store.

## Example Authentication Code

```python
import requests
import json
import hashlib
import hmac
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256

def authenticate_paprika(email, password, license_data, signature):
    # Prepare login request
    login_data = {
        'email': email,
        'password': password, 
        'data': license_data,
        'signature': signature
    }
    
    # Send login request
    response = requests.post(
        'https://www.paprikaapp.com/api/v2/account/login/',
        data=login_data
    )
    
    if response.status_code == 200:
        result = response.json()
        jwt_token = result['result']['token']
        return jwt_token
    else:
        raise Exception(f"Authentication failed: {response.status_code}")

def make_authenticated_request(endpoint, jwt_token):
    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'User-Agent': 'Paprika Recipe Manager 3/3.3.1 (Microsoft Windows NT 10.0.26100.0)'
    }
    
    response = requests.get(
        f'https://www.paprikaapp.com/api/v2/{endpoint}',
        headers=headers
    )
    
    return response.json()
```

## Conclusion

The Paprika authentication system is well-designed with multiple layers of security. However, the reliance on client-side license validation and the exposure of license data in the local database creates potential attack vectors for determined adversaries.

For legitimate API access, users must have valid Paprika licenses and account credentials. The system cannot be bypassed without either compromising the RSA private key (extremely difficult) or obtaining valid license data from legitimate purchases.