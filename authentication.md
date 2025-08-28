# Paprika Authentication Flow Documentation

## Overview

Paprika uses a dual-layer authentication system: local RSA signature validation of license data followed by server authentication that returns a JWT token for API access. Licenses are bound to specific devices via machine-specific identifiers.

## Complete Authentication Flow

### Step 1: License Data Collection

The client retrieves encrypted license data from the local SQLite database (`purchases` table). This data includes the license key, customer information, product identifier, purchase date, and a device-specific identifier (`install_uid`) that binds the license to a particular machine.

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

#### Device ID Generation

The `install_uid` field in the license binds it to a specific device. On Windows, Paprika obtains this ID from:

1. `HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Cryptography\MachineGuid` (primary)
2. `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Device` (fallback)
3. If neither exists, generates and stores a new GUID

Other platforms likely use:
- **macOS**: IOPlatformUUID from IOKit framework
- **Linux**: `/etc/machine-id` or `/var/lib/dbus/machine-id`
- **iOS**: `identifierForVendor` or keychain-stored UUID
- **Android**: `Settings.Secure.ANDROID_ID` or stored UUID

The device ID is part of the signed license data, making it tamper-evident.

### Step 2: License Validation

After decryption, the client validates the license using RSA signature verification with Paprika's public key (embedded in the application binary). The signature proves the license was issued by Paprika's servers and hasn't been modified.

```csharp
// Load Paprika's public key (embedded in app)
RsaKeyParameters publicKey = PublicKeyFactory.CreateKey(publicKeyBytes);

// Verify signature using SHA256withRSA
ISigner signer = SignerUtilities.GetSigner("SHA256withRSA");
signer.Init(false, publicKey);
signer.BlockUpdate(Encoding.UTF8.GetBytes(licenseDataJson), 0, dataBytes.Length);
bool isValid = signer.VerifySignature(Convert.FromBase64String(signature));
```

Validation also checks:
- Product ID matches expected value (e.g., "com.hindsightlabs.paprika.windows.v3")
- Device ID matches current machine
- License status (not disabled or refunded)
- Valid JSON format with required fields

### Step 3: Server Authentication

With a validated license, the client authenticates with the server by sending credentials and license data to obtain a JWT token:

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

The server responds with:

```json
{
    "result": {
        "token": "JWT-TOKEN-HERE"
    }
}
```

This token is used in all subsequent API requests:

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

The authentication process follows this sequence:
1. Load and decrypt license from SQLite database
2. Validate RSA signature and device ID
3. POST credentials and license to `/api/v2/account/login/`
4. Store returned JWT token
5. Configure HTTP client with Bearer token

JWT tokens have long expiration times (hours or days). The client revalidates licenses daily and establishes WebSocket connections for real-time sync.

## Security Implementation

### Cryptographic Protection
Licenses use RSA signatures (SHA256withRSA) that can only be created with Paprika's private key. Device binding via `install_uid` ties licenses to specific machines. Product IDs prevent cross-version license use.

### Network Security  
All API communication uses HTTPS. JWT tokens provide stateless authentication. The server independently validates license signatures.

### Known Attack Vectors
- License and token extraction from SQLite database or memory
- JWT interception via network capture (requires HTTPS compromise)
- Device ID spoofing via registry modification (Windows) or equivalent on other platforms

## Implementation Requirements

A working client requires:
1. Valid license data with RSA signature (cannot be forged without private key)
2. Matching device ID from the licensed machine
3. User account credentials (email and password)
4. HTTP client supporting multipart/form-data with specific formatting
5. JWT token handling for API requests

## Technical Summary

The authentication system uses RSA signatures for license validation and JWT tokens for session management. The RSA signature scheme prevents license forgery since only Paprika's servers have the private key. Device binding adds another validation layer but can potentially be bypassed through device ID spoofing. The system's security primarily relies on the cryptographic signature that cannot be forged without the private key.