# WhatsApp Campaign Manager

A React-based frontend application for managing WhatsApp marketing campaigns with rate limiting, duplicate prevention, and real-time tracking.

## Features

- ✅ Create and manage marketing campaigns
- ✅ Multi-step campaign creation wizard
- ✅ Auto-select recipients from target audience
- ✅ Manual recipient phone number entry
- ✅ Real-time campaign statistics
- ✅ Campaign activation and scheduling
- ✅ Pause/Resume/Cancel campaigns
- ✅ Responsive design
- ✅ Daily campaign processing trigger

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- Backend API running on `http://localhost:8000` (or configure `REACT_APP_API_URL`)

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm start
```

The app will open at [http://localhost:3000](http://localhost:3000)

### Build for Production

```bash
npm run build
```

## Configuration

### Option 1: AWS App Runner (Production)

Create a `.env` file in the root directory:

```env
REACT_APP_API_URL=https://your-app-runner-url.awsapprunner.com/api
```

Get your App Runner URL from AWS Console or CloudFormation outputs.

### Option 2: Local Development

```env
REACT_APP_API_URL=http://localhost:8000/api
```

**Note:** For local development, you need the backend running on port 8000.

## Usage

### 1. View Campaigns

The home page shows all campaigns with:
- Status badges (Draft, Active, Paused, Completed, Cancelled)
- Progress bars
- Message counts (Sent, Pending)
- Filter by status

### 2. Create Campaign

Three-step wizard:

**Step 1: Campaign Details**
- Campaign name and description
- WhatsApp template selection
- Daily send limit (max 250/day)
- Priority level
- Target audience filters

**Step 2: Add Recipients**
- Auto-select from target audience (subscribed users only)
- OR manually enter phone numbers

**Step 3: Activate Campaign**
- Set start date (optional, defaults to tomorrow)
- Campaign schedules are automatically created
- Recipients distributed across days (250/day max)

### 3. Campaign Details

View detailed statistics:
- Total recipients
- Messages sent/delivered/read/failed/pending
- Delivery and read rates
- Progress percentage
- Estimated completion date

Manage campaigns:
- Activate (from Draft)
- Pause (stop sending)
- Resume (continue sending)
- Cancel (permanently stop)

### 4. Process Daily Campaigns

Click "🚀 Process Daily" to manually trigger today's campaign sends.

**Note:** In production, this should be automated via AWS EventBridge scheduler.

## API Endpoints Used

- `POST /marketing/campaigns` - Create campaign
- `GET /marketing/campaigns` - List campaigns
- `GET /marketing/campaigns/{id}/stats` - Get campaign stats
- `POST /marketing/campaigns/{id}/recipients` - Add recipients
- `POST /marketing/campaigns/{id}/activate` - Activate campaign
- `POST /marketing/campaigns/{id}/pause` - Pause campaign
- `POST /marketing/campaigns/{id}/resume` - Resume campaign
- `POST /marketing/campaigns/{id}/cancel` - Cancel campaign
- `POST /marketing/process-daily` - Process today's campaigns

## Project Structure

```
campaign/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── CampaignList.js      # Campaign list view
│   │   ├── CreateCampaign.js    # Multi-step campaign creation
│   │   └── CampaignDetails.js   # Campaign details & management
│   ├── services/
│   │   └── api.js               # API service layer
│   ├── utils/
│   │   └── formatters.js        # Formatting utilities
│   ├── App.js                   # Main app component
│   ├── App.css                  # Global styles
│   ├── index.js                 # App entry point
│   └── index.css                # Base styles
├── package.json
└── README.md
```

## Key Features Explained

### Duplicate Prevention
The backend ensures no customer receives the same campaign twice via database UNIQUE constraint on (campaign_id, phone_number).

### Rate Limiting
Campaigns automatically respect WhatsApp's 250 messages/day limit:
- Recipients are distributed across multiple days
- Daily send schedule is created during activation
- Example: 10,000 recipients = 40 days of sending

### Subscription Respect
Only subscribed users receive campaign messages:
- Auto-selection filters for `subscription='subscribed'`
- Double-check before sending each message
- Users who unsubscribe after campaign creation are skipped

### Real-time Updates
Campaign Details page auto-refreshes every 10 seconds when status is "Active" to show live progress.

## Development

### Adding New Features

1. **New API endpoint:** Add to `src/services/api.js`
2. **New component:** Create in `src/components/`
3. **New route:** Add to `src/App.js`
4. **New formatter:** Add to `src/utils/formatters.js`

### Testing

```bash
npm test
```

### Code Style

This project uses React best practices:
- Functional components with hooks
- Async/await for API calls
- Proper error handling
- Loading states
- User confirmations for destructive actions

## Deployment

### Build and Deploy

```bash
# Build optimized production bundle
npm run build

# Deploy build/ directory to your web server
# or use with AWS S3 + CloudFront
```

### Environment Variables

Production:
```env
REACT_APP_API_URL=https://api.yourdomain.com/api
```

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

Private - WhatsApp Business Application

## Support

For issues or questions, contact your development team.
