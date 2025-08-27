# Paprika Authentication Flow Documentation

## Overview

Paprika uses a dual-layer authentication system combining:
1. **License validation** - Cryptographic signature verification using RSA
2. **Server authentication** - JWT token-based API authentication

## Complete Authentication Flow

### Step 1: License Data Collection

The client must have a valid Paprika license with these components:

#### License Data Structure
```json
{
    "key": "LICENSE-KEY-HERE",                           // License key
    "name": "USER NAME HERE",                            // Customer name  
    "email": "user@example.com",                         // Customer email
    "product_id": "com.hindsightlabs.paprika.windows.v3", // Product identifier
    "purchase_date": "2025-07-14 20:09:31",              // Purchase timestamp
    "disabled": false,                                   // Expiration/disabled status
    "refunded": false,                                   // Refund status
    "install_uid": "device-identifier-here",             // Device identifier
    "algorithm": 1                                       // Algorithm version
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
2. **Product match** - Must be for "com.hindsightlabs.paprika.windows.v3" or similar product_id
3. **Device match** - install_uid must match current machine device ID
4. **Status checks** - Not disabled or refunded
5. **License format** - Must parse as valid JSON

### Step 3: Server Authentication

With valid license, client performs server login:

#### Login API Call
```http
POST /api/v2/account/login/
Content-Type: multipart/form-data; boundary="{uuid-boundary}"
User-Agent: Paprika Recipe Manager 3/3.3.1 (Microsoft Windows NT 10.0.26100.0)
Accept-Encoding: gzip, deflate
Expect: 100-continue

--{uuid-boundary}
Content-Type: text/plain; charset=utf-8
Content-Disposition: form-data; name=email

user@example.com
--{uuid-boundary}
Content-Type: text/plain; charset=utf-8  
Content-Disposition: form-data; name=password

user_password_here
--{uuid-boundary}
Content-Type: text/plain; charset=utf-8
Content-Disposition: form-data; name=data

{license_data_json_string}
--{uuid-boundary}
Content-Type: text/plain; charset=utf-8
Content-Disposition: form-data; name=signature

{base64_signature_string}
--{uuid-boundary}--
```

**Important Details:**
- Boundary is a UUID without quotes in the Content-Type header
- Content-Type header comes BEFORE Content-Disposition in each part
- Field names have no quotes (e.g., `name=email` not `name="email"`)
- Each field value is preceded by an empty line after headers

#### Server Response
```json
{
    "result": {
        "token": "JWT-TOKEN-HERE"
    }
}
```

### Step 4: JWT Token Usage

The server returns a JSON response with the JWT token:

```json
{
    "result": {
        "token": "JWT-TOKEN-HERE"
    }
}
```

This JWT token is then used for all subsequent API calls:

```http
Authorization: Bearer JWT-TOKEN-HERE
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
    product_id TEXT,  -- "com.hindsightlabs.paprika.windows.v3"
    data TEXT,        -- Encrypted license data (Base64)
    signature TEXT,   -- Encrypted RSA signature (Base64)
    verified INTEGER  -- Last verification timestamp
);
```

**Note:** Both `data` and `signature` fields are stored encrypted using AES-256-CBC with PBKDF2 key derivation.

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
    # Prepare multipart form data
    files = {
        'email': (None, email),
        'password': (None, password),
        'data': (None, license_data),  # JSON string
        'signature': (None, signature)  # Base64 string
    }
    
    # Generate boundary and headers
    boundary = str(uuid.uuid4())
    headers = {
        'User-Agent': 'Paprika Recipe Manager 3/3.3.1 (Microsoft Windows NT 10.0.26100.0)',
        'Accept-Encoding': 'gzip, deflate',
        'Expect': '100-continue'
    }
    
    # Send login request with proper multipart formatting
    response = requests.post(
        'https://www.paprikaapp.com/api/v2/account/login/',
        files=files,
        headers=headers
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