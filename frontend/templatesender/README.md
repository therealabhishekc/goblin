# Template Sender Application

A React-based frontend application for sending WhatsApp template messages to multiple users.

## Features

- 📋 View all users from the database
- 🔍 Search users by name or phone number
- ✅ Select individual users or all users at once
- 📤 Send template messages with custom parameters
- 🎨 Support for header and body components
- 🔄 Real-time feedback on message sending status

## Installation

```bash
cd /Users/abskchsk/Documents/govindjis/wa-app/frontend/templatesender
npm install
```

## Configuration

Edit `src/config.js` to set your API URL:

```javascript
const config = {
  API_URL: 'https://your-api-url.com'
};
```

## Development

Start the development server:

```bash
npm start


```

The app will open at `http://localhost:3000`

## Production Build

Create a production build:

```bash
npm run build
```

## Usage

1. **Configure Template**: Enter the template name (e.g., `hello_world`) and language code (e.g., `en`)

2. **Add Components** (Optional): 
   - Click "Add Header" or "Add Body" to add template components
   - Add parameters for each component
   - Each parameter represents a variable in your template

3. **Select Recipients**:
   - Use the search bar to filter users
   - Click on individual users or use "Select All"
   - Selected users are highlighted in green

4. **Send**: Click the "Send" button to send the template to all selected users

## API Integration

This app integrates with the following backend endpoints:

- `GET /api/users` - Fetch all users
- `POST /messaging/template` - Send template message

## Template Message Format

The app sends messages in the following format:

```json
{
  "phone_number": "14694652751",
  "template_name": "hello_world",
  "language_code": "en",
  "components": [
    {
      "type": "body",
      "parameters": [
        {"type": "text", "text": "John"}
      ]
    }
  ]
}
```

## Notes

- Only approved WhatsApp templates can be sent
- Template names must match exactly with Meta Business approved templates
- Parameters must match the template structure in Meta Business Manager

