# Add User Frontend - WhatsApp Business

A React application for manually adding users to the WhatsApp Business database.

## Features

- ✅ Add users with phone number, name, business info, email
- 🏷️ Add custom tags to categorize users
- 🎨 Beautiful, modern UI with gradient design
- 📱 Fully responsive (mobile, tablet, desktop)
- ⚡ Real-time form validation
- 🔄 Success/Error alerts with auto-dismiss
- 🎯 Customer tier selection (Regular, Premium, VIP)

## Prerequisites

- Node.js 14+ installed
- Backend API running on `http://localhost:8000`

## Installation

1. Navigate to the frontend directory:
```bash
cd frontend/adduser
```

2. Install dependencies:
```bash
npm install
```

## Running the Application

### Development Mode

Start the development server:
```bash
npm start
```

The application will open automatically at [http://localhost:3000](http://localhost:3000)

### Production Build

Build for production:
```bash
npm run build
```

This creates an optimized production build in the `build/` directory.

## Usage

1. **Start the Backend API** (if not already running):
   ```bash
   cd ../../backend
   python start.py
   ```

2. **Start the React App**:
   ```bash
   npm start
   ```

3. **Fill in the form**:
   - **Phone Number** (required): Include country code (e.g., +1234567890)
   - **Display Name**: User's display name
   - **Business Name**: Name of their business (optional)
   - **Email**: User's email address (optional)
   - **Customer Tier**: Choose Regular, Premium, or VIP
   - **Tags**: Type tags and press Enter to add them
   - **Notes**: Any additional notes about the customer

4. **Click "Add User"** to submit

5. **Success!** The user will be added to the database and the form will reset

## API Endpoint

The app communicates with:
- **POST** `http://localhost:8000/api/users`

Request body example:
```json
{
  "whatsapp_phone": "+1234567890",
  "display_name": "John Doe",
  "business_name": "Doe's Store",
  "email": "john@example.com",
  "customer_tier": "premium",
  "tags": ["new", "high-value"],
  "notes": "Important customer"
}
```

## Project Structure

```
frontend/adduser/
├── public/
│   └── index.html          # HTML template
├── src/
│   ├── components/
│   │   ├── AddUserForm.js  # Main form component
│   │   └── AddUserForm.css # Form styles
│   ├── App.js              # Root component
│   ├── App.css             # App styles
│   ├── index.js            # Entry point
│   └── index.css           # Global styles
├── package.json            # Dependencies
└── README.md               # This file
```

## Troubleshooting

### Backend Connection Error

If you see "Network Error: Make sure the backend is running":
1. Verify the backend is running: `cd backend && python start.py`
2. Check the backend is accessible at `http://localhost:8000`
3. Test with: `curl http://localhost:8000/health`

### CORS Issues

The backend has been configured to allow requests from:
- `http://localhost:3000`
- `http://localhost:3001`

If you're running on a different port, update the CORS settings in `backend/app/main.py`

### User Already Exists

If you get "User already exists", the phone number is already in the database. Each phone number must be unique.

## Customization

### Change API URL

Edit `src/components/AddUserForm.js` line 69:
```javascript
const response = await fetch('http://YOUR_API_URL/api/users', {
```

### Modify Styling

Edit `src/components/AddUserForm.css` to customize:
- Colors
- Fonts
- Layout
- Animations

### Add More Fields

Edit `src/components/AddUserForm.js`:
1. Add field to initial state
2. Add form input in JSX
3. Update submit data

## Technologies Used

- **React 18** - UI library
- **CSS3** - Styling with animations
- **Fetch API** - HTTP requests

## Support

For issues or questions, check the backend logs and browser console for detailed error messages.
