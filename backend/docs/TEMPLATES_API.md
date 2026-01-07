# Workflow Templates API Documentation

## Overview
The Workflow Templates API provides endpoints to manage interactive menu templates for WhatsApp conversations. These templates define the structure and behavior of interactive menus that users can navigate through.

## Base URL
```
/api/templates
```

## Endpoints

### 1. List All Templates
**GET** `/api/templates/`

List all workflow templates with optional filtering.

**Query Parameters:**
- `active_only` (boolean, optional): If true, only return active templates. Default: false

**Response:**
```json
[
  {
    "id": "uuid",
    "template_name": "main_menu",
    "template_type": "button",
    "trigger_keywords": ["hi", "hello", "menu"],
    "menu_structure": {
      "initial": {
        "message": "Welcome! Choose an option:",
        "type": "button",
        "buttons": [...]
      }
    },
    "is_active": true,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
]
```

**Example:**
```bash
curl -X GET "https://2hdfnnus3x.us-east-1.awsapprunner.com/api/templates/?active_only=true"
```

---

### 2. Get Template by ID
**GET** `/api/templates/{template_id}`

Get a specific workflow template by its UUID.

**Path Parameters:**
- `template_id` (string, required): Template UUID

**Response:**
```json
{
  "id": "uuid",
  "template_name": "main_menu",
  "template_type": "button",
  "trigger_keywords": ["hi", "hello"],
  "menu_structure": {...},
  "is_active": true,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

**Example:**
```bash
curl -X GET "https://2hdfnnus3x.us-east-1.awsapprunner.com/api/templates/{template_id}"
```

---

### 3. Get Template by Name
**GET** `/api/templates/by-name/{template_name}`

Get a specific workflow template by its name.

**Path Parameters:**
- `template_name` (string, required): Template name

**Response:** Same as Get Template by ID

**Example:**
```bash
curl -X GET "https://2hdfnnus3x.us-east-1.awsapprunner.com/api/templates/by-name/main_menu"
```

---

### 4. Create Template
**POST** `/api/templates/`

Create a new workflow template.

**Request Body:**
```json
{
  "template_name": "main_menu",
  "template_type": "button",
  "trigger_keywords": ["hi", "hello", "menu"],
  "menu_structure": {
    "initial": {
      "message": "Welcome to Govindji's!",
      "type": "button",
      "buttons": [
        {
          "id": "explore",
          "title": "Explore Collection"
        },
        {
          "id": "expert",
          "title": "Talk to Expert"
        }
      ],
      "next_steps": {
        "explore": "explore_menu",
        "expert": "expert_menu"
      }
    }
  },
  "is_active": true
}
```

**Response:** Created template object

**Example:**
```bash
curl -X POST "https://2hdfnnus3x.us-east-1.awsapprunner.com/api/templates/" \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "main_menu",
    "template_type": "button",
    "trigger_keywords": ["hi", "hello"],
    "menu_structure": {...},
    "is_active": true
  }'
```

---

### 5. Update Template
**PUT** `/api/templates/{template_id}`

Update an existing workflow template.

**Path Parameters:**
- `template_id` (string, required): Template UUID

**Request Body:** (all fields optional)
```json
{
  "template_type": "button",
  "trigger_keywords": ["hi", "hello", "start"],
  "menu_structure": {...},
  "is_active": false
}
```

**Response:** Updated template object

**Example:**
```bash
curl -X PUT "https://2hdfnnus3x.us-east-1.awsapprunner.com/api/templates/{template_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": false
  }'
```

---

### 6. Delete Template
**DELETE** `/api/templates/{template_id}`

Delete a workflow template.

**Path Parameters:**
- `template_id` (string, required): Template UUID

**Response:**
```json
{
  "success": true,
  "message": "Template 'main_menu' deleted successfully",
  "template_id": "uuid"
}
```

**Example:**
```bash
curl -X DELETE "https://2hdfnnus3x.us-east-1.awsapprunner.com/api/templates/{template_id}"
```

---

### 7. Toggle Template Status
**POST** `/api/templates/{template_id}/toggle`

Enable or disable a template (toggle active status).

**Path Parameters:**
- `template_id` (string, required): Template UUID

**Response:**
```json
{
  "success": true,
  "template_id": "uuid",
  "template_name": "main_menu",
  "is_active": false,
  "message": "Template 'main_menu' disabled"
}
```

**Example:**
```bash
curl -X POST "https://2hdfnnus3x.us-east-1.awsapprunner.com/api/templates/{template_id}/toggle"
```

---

## Template Types

- `button`: Interactive button menus (max 3 buttons)
- `list`: List-based menus (max 10 items)
- `text`: Text-based menus with keyword responses

## Menu Structure Format

The `menu_structure` field contains the complete template definition:

```json
{
  "initial": {
    "message": "Welcome message",
    "type": "button|list|text",
    "buttons": [...],  // For button type
    "sections": [...], // For list type
    "next_steps": {
      "button_id": "next_step_name"
    }
  },
  "step_name": {
    // Similar structure for each step
  }
}
```

## Error Responses

All endpoints return standard error responses:

**400 Bad Request:**
```json
{
  "detail": "Invalid template ID format"
}
```

**404 Not Found:**
```json
{
  "detail": "Template {id} not found"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Failed to create template: {error message}"
}
```

## Usage Notes

1. **Template Names**: Must be unique across the system
2. **Trigger Keywords**: Case-insensitive matching
3. **Active Status**: Only active templates are used for auto-responses
4. **Menu Structure**: Must be valid JSON with proper step definitions
5. **Deletion**: Permanently removes the template from the database

## Testing

You can test the API using the interactive Swagger documentation:
```
https://2hdfnnus3x.us-east-1.awsapprunner.com/docs
```

Navigate to the "templates" section to see all available endpoints and try them out.
