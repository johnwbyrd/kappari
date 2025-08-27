# Data Schemas

JSON schemas for all Paprika API entities based on observed traffic.

## Recipe Schema

```json
{
  "uid": "string (uuid)",
  "deleted": "boolean",
  "created": "string (datetime: YYYY-MM-DD HH:MM:SS)",
  "hash": "string (sha256)",
  "name": "string",
  "description": "string",
  "ingredients": "string (multiline)",
  "directions": "string (multiline)",
  "notes": "string",
  "nutritional_info": "string",
  "prep_time": "string",
  "cook_time": "string", 
  "total_time": "string",
  "difficulty": "string",
  "servings": "string",
  "rating": "number",
  "scale": "string",
  "source": "string",
  "source_url": "string",
  "on_favorites": "boolean",
  "is_pinned": "boolean",
  "in_trash": "boolean",
  "photo": "string (filename)",
  "photo_large": "string|null",
  "photo_hash": "string (sha256)",
  "image_url": "string (url)",
  "categories": "array"
}
```

### Example Recipe
```json
{
  "uid": "C2DCBA63-0FC8-4443-9FEF-3F22C8BAEA7E",
  "deleted": false,
  "created": "2025-07-18 03:43:04",
  "hash": "FC7B9D408A079C5A7D97C5E50438E3A339E58FB90FC0EB89A67E40B7B5C10A90",
  "name": "Best Chocolate Chip Cookies",
  "description": "",
  "ingredients": "1 cup butter, softened\n1 cup white sugar\n1 cup packed brown sugar\n2 large eggs\n2 teaspoons vanilla extract\n1 teaspoon baking soda\n2 teaspoons hot water\n½ teaspoon salt\n3 cups all-purpose flour\n2 cups semisweet chocolate chips\n1 cup chopped walnuts",
  "directions": "Gather your ingredients...\n\nPreheat the oven to 350 degrees F...",
  "notes": "",
  "nutritional_info": "",
  "prep_time": "20 mins",
  "cook_time": "10 mins",
  "total_time": "",
  "difficulty": "",
  "servings": "48",
  "rating": 0,
  "scale": "",
  "source": "Allrecipes.com",
  "source_url": "https://www.allrecipes.com/recipe/10813/best-chocolate-chip-cookies/",
  "on_favorites": false,
  "is_pinned": false,
  "in_trash": false,
  "photo": "5584786F-FB5B-4DE7-A33F-A74EF5193198.jpg",
  "photo_large": null,
  "photo_hash": "803d64c6fe91efd5fa015a2573301eb84ea82869109ba3206e7bd66a559cf8f4",
  "image_url": "https://cdn.jwplayer.com/v2/media/qHQSNVCK/poster.jpg?width=720",
  "categories": []
}
```

## Menu Item Schema

```json
{
  "uid": "string (uuid)",
  "deleted": "boolean",
  "name": "string",
  "order_flag": "number",
  "day": "number",
  "menu_uid": "string (uuid)",
  "recipe_uid": "string (uuid)"
}
```

### Example Menu Item
```json
{
  "uid": "99EF09FD-B048-4D8E-A5E7-E30701D05A10",
  "deleted": true,
  "name": "Best Chocolate Chip Cookies",
  "order_flag": 3,
  "day": 1,
  "menu_uid": "BF87459F-DE27-4662-A190-9B897D2C195D",
  "recipe_uid": "C2DCBA63-0FC8-4443-9FEF-3F22C8BAEA7E"
}
```

## Field Definitions

### Common Fields
- **uid**: Unique identifier (UUID format)
- **deleted**: Soft delete flag (true = deleted)
- **created**: Creation timestamp (YYYY-MM-DD HH:MM:SS format)
- **hash**: SHA256 hash for change detection

### Recipe-Specific Fields
- **ingredients**: Newline-separated ingredient list
- **directions**: Step-by-step cooking instructions
- **prep_time/cook_time**: Human-readable time strings
- **servings**: Number or description of servings
- **rating**: Numeric rating (0-5 scale)
- **photo**: Local filename for recipe image
- **photo_hash**: SHA256 hash of image file
- **categories**: Array of category objects

### Menu Item Fields
- **order_flag**: Display order within day
- **day**: Day number in menu (1-based)
- **menu_uid**: Reference to parent menu
- **recipe_uid**: Reference to associated recipe

## To Do
- [ ] Document Menu schema
- [ ] Document Category schema  
- [ ] Document Grocery Item schema
- [ ] Document Photo/Media schemas
- [ ] Validate field types and constraints
- [ ] Document array/object subschemas
- [ ] Add validation rules and required fields