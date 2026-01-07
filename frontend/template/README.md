# Template Manager

A React-based interface for managing WhatsApp interactive menu templates.

## Features

- 📋 View all workflow templates
- ➕ Create new templates
- ✏️ Edit existing templates
- 🗑️ Delete templates
- 🔍 Preview menu structures
- 🎨 Clean and intuitive UI

## Getting Started

### Prerequisites

- Node.js 14+ and npm

### Installation

```bash
cd frontend/template
npm install
```

### Development

```bash
npm start
```

The app will run on `http://localhost:3000`

### Build for Production

```bash
npm run build
```

## Template Structure

Templates consist of:
- **Template Name**: Unique identifier
- **Template Type**: button, list, or text
- **Trigger Keywords**: Keywords that activate the template
- **Menu Structure**: Message content and interactive elements
- **Status**: Active/Inactive flag

## API Integration

The app connects to the backend API at:
`https://2hdfnnus3x.us-east-1.awsapprunner.com`

Endpoints:
- `GET /api/templates` - List all templates
- `POST /api/templates` - Create template
- `PUT /api/templates/{id}` - Update template
- `DELETE /api/templates/{id}` - Delete template
