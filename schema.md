# Paprika Database Schema Documentation

This document describes the SQLite database schema used by Paprika Recipe Manager 3, based on reverse engineering of the application, network traffic analysis, and decompiled source code examination.

## General Patterns and Conventions

### UID Generation

All entities in Paprika use uppercase UUID identifiers following the standard `XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX` format. These UIDs serve as immutable primary keys throughout the schema. Unlike auto-incrementing integers, UUIDs enable conflict-free synchronization across multiple devices because each device can generate unique identifiers independently without requiring coordination with other devices or a central server.

### Hash Algorithms

Paprika employs two distinct SHA256 hashing systems for different purposes. The sync_hash field implements a change tracking mechanism that generates unique random tokens rather than hashing entity content. When an entity is modified, the system generates a new GUID, immediately hashes it with SHA256, and stores the result as the sync_hash. The original GUID is discarded and cannot be recovered.

The photo_hash field serves a different purpose, containing SHA256 hashes of actual photo file contents. This enables integrity verification and duplicate detection across the photo library.

Both hashing systems produce 64-character uppercase hexadecimal strings representing the 32-byte SHA256 output. However, their inputs and purposes are fundamentally different: sync_hash tracks entity changes through random tokens, while photo_hash verifies file content integrity.

### Status Field Values

The status field uses simple string values to track entity modification state. Based on database examination, the field contains "unmodified" for entities that have not been changed locally, and presumably "modified" for entities that have local changes awaiting synchronization.

### Change Tracking System

Tables that participate in synchronization implement a standard pattern using three fields: sync_hash for change detection, status for modification tracking, and is_synced for local state management. When an entity is modified locally, the system generates a new sync_hash token, updates the status field from "unmodified" to "modified", and sets is_synced to false (0).

The change detection mechanism compares sync_hash values between local and server copies of entities. Since these hashes are generated from random GUIDs and change with every modification, they provide a reliable method for identifying updated entities without requiring timestamp comparison or content analysis.

The system implements soft deletes throughout the schema, meaning that deleted entities are likely marked with a specific status value (though the exact mechanism requires further investigation) rather than being physically removed from the database.

### Photo Storage Architecture

Paprika stores photos in the filesystem rather than as database blobs, using a hierarchical directory structure for organization and performance. Photos are stored at `Photos/{recipe_uid}/{photo_filename}.jpg` where each recipe receives its own subdirectory identified by the recipe's UID. Photo filenames are themselves UUIDs to ensure uniqueness and prevent naming conflicts.

The recipes table references primary photos through the photo field, which contains only the filename. The application constructs the full path by combining the recipe's UID with this filename. Additional photos beyond the primary image are tracked in the recipe_photos table, which maintains metadata including display order, download status, and synchronization state.

File integrity is maintained through photo_hash fields containing SHA256 hashes of the actual file contents. This system serves multiple purposes: verifying that files have not been corrupted, detecting duplicate photos across different recipes, and ensuring that database references correspond to the correct file contents.

### Data Type Conventions

Boolean values are stored as integers in SQLite (0 for false, 1 for true) following SQLite's standard convention, but these values are transformed into JSON boolean types in API responses.

Date and time handling uses SQLite's Julian date system for internal storage.

Text encoding uses UTF-8 consistently throughout the database to ensure proper support for international characters and cooking terminology in multiple languages. The schema preserves the distinction between NULL values and empty strings, which carries semantic meaning in the synchronization logic where NULL often indicates uninitialized fields while empty strings represent intentionally blank content.

## Full-Text Search System

Paprika implements recipe search functionality using SQLite's FTS5 extension. The search system mirrors textual content from the main recipes table, in a specialized virtual table that enables efficient query processing across large recipe collections.

The search index is maintained automatically through database triggers that ensure synchronization between recipe content and search data.

## Synchronization Protocol

Paprika implements a multi-device synchronization system that maintains data consistency across devices while handling offline modifications and conflict resolution. The synchronization architecture combines change tracking tokens, status-based change management, and content verification to ensure reliable data sharing without data loss or corruption.

Change detection works via the sync_hash mechanism implemented across all synchronized tables. Each entity includes a sync_hash field containing a SHA256 hash generated from a random GUID. When entities are modified locally, the system generates a completely new random GUID, hashes it with SHA256, and stores the result as the updated sync_hash. This approach creates cryptographically secure change detection tokens that reliably indicate when entities have been modified without revealing any information about the actual content changes.

Status lifecycle management tracks entities with string status values. Entities show "unmodified" when they match the server state, and the system likely uses "modified" or similar values to indicate local changes awaiting synchronization.

The soft delete architecture prevents deleted content from reappearing when offline devices reconnect to the synchronization system. Rather than immediately removing deleted entities from the database, the system marks them appropriately and retains them until all connected devices have received and acknowledged the deletion notification.

### API vs Database Field Mapping

The synchronization system bridges two distinct data representations: the internal SQLite database structure optimized for local operations and performance, and the JSON API format.

The database includes several implementation-specific fields that are never exposed through the API. The auto-incrementing id field serves as a primary key for local database operations and joins. The status field manages synchronization state internally. The is_synced flag tracks local synchronization completion. The sync_hash field provides change detection tokens for the synchronization protocol.

Julian date values are converted to ISO timestamp strings, and internal sync_hash values become the API's hash field with appropriate formatting transformations.

## Database Tables

### recipes

#### Purpose

Core recipe storage with full recipe data, metadata, sync status, and photo references.

#### Schema

| Column | Type | Description | Example Values |
| --- | --- | --- | --- |
| id | INTEGER PRIMARY KEY | Internal database auto-increment ID | 1, 2, 3... |
| uid | TEXT | Unique UUID identifier for recipe used for sync and photo directory organization | "E5BCA7D4-7FAB-4B1B-AC14-7D5C843B56FA" |
| status | TEXT | Synchronization status indicator | "unmodified" |
| name | TEXT | Recipe title/name | "Best Vegetarian Chili in the World" |
| ingredients | TEXT | Complete ingredient list with quantities, newline-separated | "1 tablespoon olive oil\n½ medium onion, chopped\n2 tablespoons dried oregano..." |
| directions | TEXT | Step-by-step cooking instructions with paragraph formatting | "Gather all ingredients.\n\nHeat olive oil in a large pot over medium heat..." |
| description | TEXT | Recipe description, summary, or user notes (combines description and notes functionality) | NULL (most recipes) |
| nutritional_info | TEXT | Nutritional information data | NULL (observed) |
| servings | TEXT | Number of servings recipe makes as free text | "4 servings", "One serving", "8 1-cup servings" |
| difficulty | TEXT | Recipe difficulty level | NULL (observed) |
| prep_time | TEXT | Preparation time | NULL, "35 min" |
| cook_time | TEXT | Cooking/baking time | NULL |
| total_time | TEXT | Total time from start to finish | "35", NULL |
| rating | INTEGER | User's star rating on 0-5 scale, 0 means unrated | 0, 3, 4 |
| in_trash | BOOLEAN | Whether recipe is soft deleted | 0 (FALSE) observed |
| is_pinned | BOOLEAN | Whether recipe is pinned for quick access | 0 (FALSE) observed |
| is_synced | BOOLEAN | Whether recipe is synchronized with server | 0/1 |
| on_favorites | BOOLEAN | Whether recipe is marked as favorite | 0/1 |
| source | TEXT | Recipe source attribution | NULL (most recipes) |
| source_url | TEXT | Original URL if recipe was imported from web | NULL (observed) |
| image_url | TEXT | URL of recipe image from external source | NULL (observed) |
| photo | TEXT | Primary photo filename stored at Photos/{recipe_uid}/{filename} | "BC6BFB89-1301-445C-AB7F-61FF0410E122.jpg", NULL |
| photo_hash | TEXT | SHA256 hash of primary photo file contents for integrity verification | "78B7C5E6901B115E60B9D8C21373AE226C5CCB7F5D00537974D058869EB7E227" |
| photo_large | TEXT | Large version photo filename, different from primary photo, stored in same directory | "25E502DA-91D2-45EA-8852-10740D004EE6.jpg", NULL |
| photo_is_downloaded | BOOLEAN | Whether primary photo has been downloaded locally | 0/1 |
| photo_is_uploaded | BOOLEAN | Whether primary photo has been uploaded to server | 0/1 |
| scale | TEXT | Recipe scaling factor for adjusting serving sizes | NULL (observed) |
| selected_ingredients | TEXT | UI state tracking which ingredients are currently selected/highlighted | NULL (observed) |
| selected_direction | TEXT | UI state tracking which direction step is currently selected | NULL (observed) |
| sync_hash | TEXT | SHA256 hash of random GUID for change detection in sync system | "a52e2b5870676cb78d22f608f0dfba867e3417de52f42bf63dfaab7ec8568383" |
| created | DATETIME | Recipe creation timestamp | Date strings |
