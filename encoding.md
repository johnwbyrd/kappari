# Request/Response Encoding

## Request Format

### Content-Type
All POST requests use multipart form data:
```http
Content-Type: multipart/form-data; boundary="{random-uuid}"
```

### Multipart Structure
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
Authorization: Bearer {token}
Content-Type: multipart/form-data; boundary="{boundary}"
Content-Length: {length}
Accept-Encoding: gzip, deflate
User-Agent: Paprika Recipe Manager 3/3.3.1 (Microsoft Windows NT 10.0.26100.0)
Host: www.paprikaapp.com
Expect: 100-continue
```

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
```http
--boundary-uuid
Content-Disposition: form-data; name=data; filename=file; filename*=utf-8''file

{gzipped-binary-data}
--boundary-uuid--
```

## Decompression Example

### Extract gzip data from multipart:
1. Find multipart boundary
2. Extract data between headers and boundary
3. Decompress with gzip
4. Parse resulting JSON

## Implementation Notes
- Boundary UUIDs are random for each request
- Form field is always named `data`
- Filename attributes are always `file`
- Gzip compression is mandatory for request bodies
- Response decompression depends on server's Content-Encoding header