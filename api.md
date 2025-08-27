# Paprika API v2 Overview

This documents API version 2, which is used by Paprika 3. There is an older v1 API that is not covered here.

## Base URL
```
https://www.paprikaapp.com/api/v2/
```

## API Conventions

### URL Structure
- All endpoints follow the pattern: `/api/v2/sync/{entity}/`
- Individual resources: `/api/v2/sync/{entity}/{uuid}/`
- Uses UUIDs for all entity identifiers

### HTTP Methods
- `GET` - Retrieve data (not commonly observed)
- `POST` - Create or update entities
- `DELETE` - Remove entities (likely via deleted flag)

### Authentication
- Bearer token authentication using JWT
- Token obtained via `/api/v2/account/login/` endpoint
- Token included in `Authorization: Bearer {token}` header for subsequent requests
- Login requires valid license data and RSA signature along with credentials

### User Agent
All requests include:
```
User-Agent: Paprika Recipe Manager 3/3.3.1 (Microsoft Windows NT 10.0.26100.0)
```

## Entity Types

Based on observed traffic:

- **Recipes** - Individual recipe data with ingredients, directions, metadata
- **Menu Items** - Planned meals linking recipes to specific days
- **Menus** - Collections of menu items for meal planning
- **Categories** - Recipe organization tags
- **Grocery Lists** - Shopping lists derived from meal plans

## Request/Response Format

### Requests
- `Content-Type: multipart/form-data; boundary="{uuid}"`
- For authentication: plain text multipart fields
- For data sync: gzip-compressed JSON in form field
- Multipart format: Content-Type header before Content-Disposition
- Field names without quotes in Content-Disposition header
- Standard HTTP headers for compression negotiation

### Responses
- JSON format
- May be gzip compressed based on Accept-Encoding
- Standard HTTP status codes

## Sync Architecture

The API appears to implement a bi-directional sync system:
- Client sends local changes to server
- Server responds with updates needed by client
- Uses timestamps and UUIDs for conflict resolution
- Soft deletes via `deleted: true` flags

## Next Steps

- [Authentication](authentication.md) - How to obtain and use access tokens
- [Encoding](encoding.md) - Details on multipart/gzip encoding
- [Endpoints](endpoints.md) - Complete list of available operations