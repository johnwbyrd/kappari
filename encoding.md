# Request/Response Encoding

## Request Format

### Content-Type
All POST requests use multipart form data:
```http
Content-Type: multipart/form-data; boundary="{uuid-without-quotes}"
```

**Note:** The boundary is a UUID string without quotes in the Content-Type header.

### Multipart Structure

For authentication and standard API calls:
```http
--{boundary}
Content-Type: text/plain; charset=utf-8
Content-Disposition: form-data; name={field_name}

{field_value}
--{boundary}--
```

**Important:** 
- Content-Type header comes BEFORE Content-Disposition
- Field names have no quotes (e.g., `name=email` not `name="email"`)
- Empty line between headers and content

For compressed data uploads (recipes, etc.):
```http
--{boundary}
Content-Disposition: form-data; name=data; filename=file; filename*=utf-8''file

{gzip-compressed-json}
--{boundary}--
```

### Compression
Request bodies are gzip compressed:
- JSON data is compressed using gzip (RFC 1952)
- Magic bytes: `1F 8B` at start of compressed data
- Compression method: deflate (08)

### Headers
Required headers for requests:
```http
User-Agent: Paprika Recipe Manager 3/3.3.1 (Microsoft Windows NT 10.0.26100.0)
Accept-Encoding: gzip, deflate
Expect: 100-continue
Content-Type: multipart/form-data; boundary="{uuid}"
Content-Length: {length}
Authorization: Bearer {token}  # Only for authenticated requests
Host: www.paprikaapp.com
```

**Note:** For login requests, Authorization header is not included since you're obtaining the token.

## Response Format

### Content-Type
Responses are JSON:
```http
Content-Type: application/json
```

### Compression
Responses may be gzip compressed based on request Accept-Encoding header.

## Character Encoding
- All text data uses UTF-8 encoding
- JSON strings properly escape Unicode characters
- Binary data (images) handled separately

## Example Request Encoding

### 1. Create JSON payload:
```json
{
  "uid": "12345-67890-ABCDEF",
  "name": "Chocolate Chip Cookies",
  "ingredients": "1 cup flour\n2 eggs"
}
```

### 2. Gzip compress the JSON:
```bash
echo '{"uid":"12345"...}' | gzip
```

### 3. Wrap in multipart form:

For authentication (plain text fields):
```http
--{uuid-boundary}
Content-Type: text/plain; charset=utf-8
Content-Disposition: form-data; name=data

{json-string}
--{uuid-boundary}--
```

For compressed uploads:
```http
--{uuid-boundary}
Content-Disposition: form-data; name=data; filename=file; filename*=utf-8''file

{gzipped-binary-data}
--{uuid-boundary}--
```

## Decompression Example

### Extract gzip data from multipart:
1. Find multipart boundary
2. Extract data between headers and boundary
3. Decompress with gzip
4. Parse resulting JSON

## Implementation Notes
- Boundary UUIDs are random for each request (formatted without quotes in Content-Type)
- For authentication: fields are `email`, `password`, `data`, `signature`
- For data sync: field is typically `data` with compressed content
- Content-Type header must come before Content-Disposition in multipart parts
- Field names in Content-Disposition have no quotes
- Gzip compression is used for recipe/sync data, not for authentication
- Response decompression depends on server's Content-Encoding header