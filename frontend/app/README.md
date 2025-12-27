# WhatsApp CRM - Modern Glassmorphism UI

A modern, responsive CRM application with glassmorphism design that works seamlessly on both mobile and web platforms.

## Features

- 🎨 **Glassmorphism Design** - Modern, beautiful UI with glass effects
- 📱 **Responsive** - Works perfectly on mobile and desktop
- ⚡ **Fast** - Built with React for optimal performance
- 🔐 **Secure** - JWT authentication and protected routes
- 📊 **Analytics** - Real-time dashboard with key metrics
- 💬 **Messaging** - WhatsApp business messaging integration
- 🎯 **Campaigns** - Marketing campaign management
- 👥 **User Management** - Admin and user role management

## Getting Started

### Prerequisites

- Node.js 14+ installed
- Backend API running (see backend folder)

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create `.env` file:
```bash
cp .env.example .env
```

3. Update the `.env` file with your API URL

### Running the App

Development mode:
```bash
npm start
```

Production build:
```bash
npm run build
```

## Project Structure

```
src/
├── components/     # Reusable UI components
├── pages/          # Page components
├── services/       # API services
├── contexts/       # React contexts (Auth, etc.)
├── hooks/          # Custom React hooks
├── styles/         # Global styles and themes
├── utils/          # Utility functions
├── config.js       # App configuration
├── App.js          # Main app component
└── index.js        # Entry point
```

## Available Pages

- **Dashboard** - Overview with key metrics and recent activity
- **Messages** - Send and manage WhatsApp messages
- **Campaigns** - Create and manage marketing campaigns
- **Users** - User management and permissions
- **Analytics** - Detailed analytics and reports
- **Archive** - Message and media archive
- **Settings** - App and user settings

## Design System

The app uses a modern glassmorphism design with:
- Frosted glass effects with backdrop blur
- Smooth animations and transitions
- Gradient backgrounds
- Responsive grid layouts
- Custom scrollbars
- Mobile-first approach

## API Integration

The app connects to the backend API with the following features:
- RESTful API calls using Axios
- WebSocket for real-time updates
- JWT token authentication
- Automatic token refresh
- Error handling and retry logic

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Contributing

1. Create a feature branch
2. Make your changes
3. Test on both mobile and desktop
4. Submit a pull request

## License

MIT
