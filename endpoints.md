# API Endpoints

## Base URL
```
https://www.paprikaapp.com/api/v2/
```

## Endpoint Patterns

### Sync Endpoints
Most operations use the sync endpoint pattern:
```
POST /api/v2/sync/{entity}/
POST /api/v2/sync/{entity}/{uuid}/
```

## Discovered Endpoints

### Authentication
```http
POST /api/v2/account/login/
```
- **Purpose**: Authenticate user and obtain JWT token
- **Request**: Multipart form data with email, password, license data, and signature
- **Response**: JSON with JWT token in `result.token`

### Menu Items
```http
POST /api/v2/sync/menuitems/
```
- **Purpose**: Sync menu item data (meal planning)
- **Request**: Gzip-compressed JSON array of menu items
- **Response**: JSON with sync status

### Recipes
```http
POST /api/v2/sync/recipe/{recipe-uuid}/
```
- **Purpose**: Sync individual recipe data
- **Request**: Gzip-compressed recipe JSON
- **Response**: JSON with sync confirmation

*[Additional endpoints to be documented as discovered]*

## Common Request Format

### Headers
```http
Authorization: Bearer {jwt-token}
Content-Type: multipart/form-data; boundary="{boundary}"
Accept-Encoding: gzip, deflate
User-Agent: Paprika Recipe Manager 3/3.3.1 (Microsoft Windows NT 10.0.26100.0)
Content-Length: {length}
Expect: 100-continue
```

### Body Structure
```http
--{boundary}
Content-Disposition: form-data; name=data; filename=file; filename*=utf-8''file

{gzip-compressed-json-payload}
--{boundary}--
```

## Response Format

### Success Response
```json
{
  "result": true
}
```

### Error Responses
*[To be documented when encountered]*

## HTTP Status Codes
- `200 OK` - Successful operation
- *[Additional status codes to be documented]*

## Endpoint Discovery Status

### Confirmed Endpoints
- [x] `/api/v2/account/login/` - User authentication
- [x] `/api/v2/sync/menuitems/` - Menu item synchronization
- [x] `/api/v2/sync/recipe/{uuid}/` - Individual recipe sync

### Likely Endpoints (Not Yet Confirmed)
- [ ] `/api/v2/sync/recipes/` - Bulk recipe operations
- [ ] `/api/v2/sync/menus/` - Menu/meal plan management
- [ ] `/api/v2/sync/categories/` - Recipe categories
- [ ] `/api/v2/sync/groceryitems/` - Grocery list items
- [x] `/api/v2/account/login/` - Authentication endpoint (CONFIRMED)
- [ ] `/api/v2/photos/` - Recipe photo upload/download

## To Do
- [ ] Document all endpoints found in captured traffic
- [ ] Map request/response schemas for each endpoint
- [ ] Document error responses and status codes
- [ ] Identify batch vs individual operations
- [ ] Document photo/media endpoints