# API Patterns

Common sequences and patterns observed in Paprika API usage.

## Sync Patterns

### Menu Item Sync
Menu items are typically synchronized as arrays of objects:

```http
POST /api/v2/sync/menuitems/
```

**Request Payload** (after decompression):
```json
[
  {
    "uid": "99EF09FD-B048-4D8E-A5E7-E30701D05A10",
    "deleted": true,
    "name": "Best Chocolate Chip Cookies",
    "order_flag": 3,
    "day": 1,
    "menu_uid": "BF87459F-DE27-4662-A190-9B897D2C195D",
    "recipe_uid": "C2DCBA63-0FC8-4443-9FEF-3F22C8BAEA7E"
  }
]
```

### Individual Recipe Sync
Recipes are synchronized individually by UUID:

```http
POST /api/v2/sync/recipe/{recipe-uuid}/
```

**Request Payload** (after decompression):
```json
{
  "uid": "C2DCBA63-0FC8-4443-9FEF-3F22C8BAEA7E",
  "name": "Best Chocolate Chip Cookies",
  "ingredients": "1 cup butter...",
  "directions": "Gather ingredients...",
  ...
}
```

## Common Response Pattern

Most successful operations return:
```json
{
  "result": true
}
```

## Deletion Pattern

Entities use soft deletes via the `deleted` flag rather than actual removal:

```json
{
  "uid": "99EF09FD-B048-4D8E-A5E7-E30701D05A10",
  "deleted": true,
  ...
}
```

## Bulk vs Individual Operations

### Bulk Operations
- Menu items: Sent as arrays
- Categories: Likely arrays (to be confirmed)
- Grocery items: Likely arrays (to be confirmed)

### Individual Operations  
- Recipes: One recipe per request
- Photos: Individual upload/download (to be confirmed)

## Startup Sync Sequence

*[To be documented based on app startup traffic analysis]*

Likely pattern:
1. Authentication/token validation
2. Fetch remote changes since last sync
3. Push local changes to server
4. Handle conflicts and merge

## Change Detection

### Hash-Based Detection
Recipes use SHA256 hashes for change detection:
- `hash`: Content hash for the recipe data
- `photo_hash`: Separate hash for recipe images

### Timestamp-Based Detection
- `created`: Entity creation time
- Additional timestamp fields likely exist for modification tracking

## Error Handling Patterns

*[To be documented when errors are observed]*

## Compression Patterns

### Request Compression
- All POST request bodies are gzip compressed
- Compression is mandatory, not optional
- Typical compression ratio: ~40-50% size reduction

### Response Compression
- Responses may be compressed based on Accept-Encoding
- Client requests: `Accept-Encoding: gzip, deflate`

## UUID Patterns

All entity identifiers follow standard UUID format:
- Format: `XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX`
- Case: Uppercase letters
- Used for recipes, menus, menu items, categories, etc.

## To Do
- [ ] Document complete startup sync sequence
- [ ] Map out conflict resolution patterns
- [ ] Document error response patterns
- [ ] Analyze photo upload/download patterns
- [ ] Document pagination (if any)
- [ ] Map dependencies between entity types