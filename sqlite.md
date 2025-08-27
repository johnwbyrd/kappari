# Paprika SQLite Database Documentation

## Overview

Paprika stores its local data in an SQLite database located at:
- Windows: `C:\Users\[Username]\AppData\Local\Paprika Recipe Manager 3\Database\Paprika.sqlite`
- The database serves as a local cache that syncs with Paprika's cloud servers

## Key Tables

### recipes
Primary table for storing recipe data.

#### Important Columns:
- `uid` (TEXT PRIMARY KEY) - GUID in uppercase format (e.g., 'A2269D0E-9E1E-4A97-9DD0-2D5ED94A0F1E')
- `status` (TEXT) - Sync status: 'new', 'modified', 'synced', or 'deleted'
- `sync_hash` (TEXT) - **Critical**: SHA256 hash for sync tracking (64 hex characters)
- `name` (TEXT) - Recipe name
- `ingredients` (TEXT) - Ingredients list
- `directions` (TEXT) - Cooking directions
- `created` (REAL) - Julian date timestamp
- `is_synced` (INTEGER) - Boolean (0 or 1)

### recipes_search
Full-text search (FTS4) table that must be kept in sync with the recipes table.

### Other Entity Tables
All sync entities follow similar patterns:
- `groceries` - Grocery list items
- `grocery_aisles` - Aisle categories
- `grocery_lists` - Shopping lists
- `meals` - Meal calendar entries
- `menus` - Menu collections
- `menu_items` - Items within menus
- `categories` - Recipe categories
- `bookmarks` - Web bookmarks
- `pantry` - Pantry inventory

## Sync Hash Generation

The `sync_hash` field is **critical** for synchronization. It's not a content hash but a change tracking mechanism.

### Algorithm:
```csharp
// Generate new GUID
string guid = Guid.NewGuid().ToString().ToUpper();
// Create SHA256 hash
byte[] hash = SHA256.Create().ComputeHash(Encoding.UTF8.GetBytes(guid));
// Format as hex string without dashes
string sync_hash = BitConverter.ToString(hash).Replace("-", "");
```

### Example Implementation:
```python
import hashlib
import uuid

def generate_sync_hash():
    # Generate new GUID and convert to uppercase
    guid = str(uuid.uuid4()).upper()
    # Create SHA256 hash
    hash_bytes = hashlib.sha256(guid.encode('utf-8')).digest()
    # Convert to hex string
    return hash_bytes.hex().upper()
```

### When Sync Hash Changes:
1. **Object created locally**: Gets new random hash
2. **Object modified locally**: Gets NEW random hash
3. **Object synced from server**: Uses server's hash value

## Status Field Values

Encrypted string keys and their meanings:
- `44433` → "new" - Newly created locally
- `44497` → "synced" - In sync with server
- `41553` → "deleted" - Marked for deletion
- `44295` → (another valid sync state)

## Required Steps for Manual Recipe Insertion

To insert a recipe that will properly sync with Paprika servers:

### 1. Generate Valid IDs
```sql
-- Generate GUID for uid (must be uppercase)
-- Generate sync_hash using the algorithm above
```

### 2. Insert into recipes Table
```sql
INSERT INTO recipes (
    uid, 
    name, 
    ingredients, 
    directions, 
    status, 
    is_synced, 
    created,
    sync_hash
) VALUES (
    'YOUR-GUID-HERE',
    'Recipe Name',
    'Ingredient list',
    'Directions',
    'new',           -- Must be 'new' for locally created
    1,               -- Mark as needing sync
    julianday('now'), -- Current timestamp
    'YOUR-SYNC-HASH-HERE'
);
```

### 3. Update FTS Table
```sql
INSERT INTO recipes_search (
    docid,
    name,
    ingredients,
    directions,
    description,
    notes,
    source
) SELECT 
    id,
    name,
    ingredients,
    directions,
    description,
    notes,
    source
FROM recipes 
WHERE uid = 'YOUR-GUID-HERE';
```

### 4. Handle Recipe Categories
If adding categories, use the `recipe_categories` junction table:
```sql
INSERT INTO recipe_categories (recipe_id, category_id)
SELECT r.id, c.id 
FROM recipes r, categories c 
WHERE r.uid = 'YOUR-RECIPE-UID' 
AND c.uid = 'YOUR-CATEGORY-UID';
```

## Important Sync Behaviors

### Server Validation
- The server validates the sync_hash format (must be 64 hex characters)
- Invalid hashes cause sync failures and retry loops
- The server uses sync_hash to detect changes, not content validation

### Change Detection
During sync, Paprika compares local vs server sync hashes:
- If different: Downloads server version (server wins)
- If same: No action needed
- Empty/invalid hash: Sync fails

### Sync Loop Prevention
To avoid the sync loop issue:
1. Always use properly formatted sync_hash (64 hex chars)
2. Set status to 'new' for locally created items
3. Ensure is_synced = 1 for items needing sync

## Database Files

Paprika uses SQLite with Write-Ahead Logging (WAL):
- `Paprika.sqlite` - Main database file
- `Paprika.sqlite-shm` - Shared memory file
- `Paprika.sqlite-wal` - Write-ahead log

All three files work together; modifying the database requires all to be in sync.

## Entity Relationships

### Recipe-Related Tables
- `recipes` ↔ `categories` (many-to-many via `recipe_categories`)
- `recipes` ↔ `photos` (one-to-many)
- `recipes` → `meals` (via recipe_uid)
- `recipes` → `menu_items` (via recipe_uid)

### Grocery-Related Tables
- `grocery_lists` → `groceries` (via list_uid)
- `grocery_aisles` → `groceries` (via aisle_uid)
- `grocery_aisles` → `pantry` (via aisle_uid)

## Common Pitfalls

1. **Missing FTS Updates**: Recipes won't appear in search if recipes_search isn't updated
2. **Invalid Sync Hash**: Must be exactly 64 hex characters (SHA256 output)
3. **Wrong Status**: Using 'synced' for new items prevents upload
4. **Boolean Fields**: SQLite uses 0/1, not true/false
5. **Date Format**: Uses Julian dates (days since Nov 24, 4714 BC)

## Useful Queries

### Find Recipes Without Valid Sync Hash
```sql
SELECT uid, name, sync_hash, length(sync_hash) as hash_length
FROM recipes 
WHERE sync_hash IS NULL 
   OR length(sync_hash) != 64
   OR sync_hash NOT GLOB '[0-9A-F]*';
```

### Mark Recipe for Re-sync
```sql
UPDATE recipes 
SET status = 'modified',
    sync_hash = 'NEW-HASH-HERE',
    is_synced = 1
WHERE uid = 'RECIPE-UID';
```

### Clean Orphaned Categories
```sql
DELETE FROM recipe_categories 
WHERE recipe_id NOT IN (SELECT id FROM recipes);
```