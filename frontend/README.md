# Modern Frontend for Arsa Analiz ve Sunum Platformu

This is a modern, API-driven frontend built from scratch for the real estate analysis and CRM platform.

## 🚀 Features

- **Modern Architecture**: Built with vanilla JavaScript ES6+ modules
- **API-First Design**: Consumes data exclusively from REST API endpoints
- **JWT Authentication**: Secure token-based authentication with auto-refresh
- **Responsive Design**: Mobile-first design using Tailwind CSS
- **Real-time Updates**: Live data updates and notifications
- **Modular Structure**: Clean, maintainable code organization

## 📋 Pages

### 🏠 Dashboard
- Real-time statistics and KPIs
- Interactive charts (Chart.js)
- Recent activities and quick actions
- Auto-refreshing data

### 👥 CRM
- Contact management with search and filtering
- Company, deals, and tasks management
- Tabbed interface for different entity types
- CRUD operations with modal forms

### 📊 Analysis
- Property analysis listing and management
- Advanced filtering and search
- Grid/list view toggle
- Status tracking and reporting

### 📁 Portfolio
- Portfolio creation and management
- Analysis grouping and organization
- Value tracking and statistics
- Tag-based categorization

### 👤 Profile
- User profile management
- Password change functionality
- Preferences and settings
- Account statistics

## 🛠️ Technology Stack

- **JavaScript**: ES6+ modules, async/await
- **CSS**: Tailwind CSS + SCSS
- **Build Tool**: Webpack 5
- **HTTP Client**: Axios
- **Charts**: Chart.js
- **Authentication**: JWT tokens with refresh mechanism

## 📁 Project Structure

```
frontend/
├── src/
│   ├── js/
│   │   ├── api/           # API client and authentication
│   │   │   ├── client.js  # HTTP client wrapper
│   │   │   └── auth.js    # Authentication service
│   │   ├── pages/         # Page components
│   │   │   ├── dashboard.js
│   │   │   ├── crm.js
│   │   │   ├── analysis.js
│   │   │   ├── portfolio.js
│   │   │   └── profile.js
│   │   ├── utils/         # Utility classes
│   │   │   ├── router.js      # Client-side routing
│   │   │   ├── ui-manager.js  # UI state management
│   │   │   └── toast-manager.js # Notifications
│   │   └── app.js         # Main application
│   ├── css/
│   │   └── main.scss      # Main stylesheet
│   └── index.html         # HTML template
├── dist/                  # Built files
└── README.md
```

## 🚀 Getting Started

### Prerequisites
- Node.js 16+ and npm
- Running Flask API server on port 5000

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm run frontend:dev
```

3. Build for production:
```bash
npm run frontend:build
```

### Development Server
The frontend development server runs on `http://localhost:3001` and proxies API requests to `http://localhost:5000`.

## 🔧 Configuration

### API Endpoints
The frontend expects the following API structure:

```
/api/v1/
├── /auth          # Authentication
├── /users         # User management
├── /crm           # CRM operations
├── /analysis      # Property analysis
└── /portfolio     # Portfolio management
```

### Environment Variables
No environment variables required for development. The API base URL is automatically configured.

## 🎨 UI Components

### Custom CSS Classes
- `.btn` - Button styles with variants (primary, secondary, etc.)
- `.card` - Card container with header, body, footer
- `.form-group` - Form field grouping
- `.table` - Responsive table styling
- `.badge` - Status badges
- `.alert` - Alert messages

### Responsive Design
- Mobile-first approach
- Breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px)
- Responsive navigation and layouts

## 🔐 Authentication Flow

1. **Login**: User enters credentials
2. **Token Storage**: Access and refresh tokens stored in localStorage
3. **Auto-Refresh**: Tokens automatically refreshed before expiration
4. **API Requests**: All requests include Bearer token
5. **Logout**: Tokens cleared and user redirected

## 📱 Features

### Real-time Updates
- Dashboard auto-refreshes every 5 minutes
- Toast notifications for user feedback
- Loading states for better UX

### Error Handling
- Network error recovery
- User-friendly error messages
- Graceful degradation

### Accessibility
- Keyboard navigation support
- Screen reader friendly
- Focus management
- ARIA labels

## 🧪 Testing

### Manual Testing
1. Start the Flask API server
2. Start the frontend development server
3. Navigate to `http://localhost:3001`
4. Test authentication and page navigation

### API Testing
The frontend includes built-in API health checks and error handling for robust operation.

## 🚀 Deployment

### Production Build
```bash
npm run frontend:build
```

### Static File Serving
The built files in `frontend/dist/` can be served by any static file server or integrated with the Flask application.

## 🔄 Integration with Flask

The frontend is designed to work alongside the existing Flask application:

1. **Development**: Runs on separate port with API proxy
2. **Production**: Can be served as static files from Flask
3. **API**: Consumes existing Flask API endpoints

## 📈 Performance

- **Code Splitting**: Vendor libraries separated
- **Asset Optimization**: Images and fonts optimized
- **Caching**: Browser caching for static assets
- **Lazy Loading**: Components loaded on demand

## 🛡️ Security

- **JWT Tokens**: Secure authentication
- **HTTPS Ready**: Production-ready security headers
- **XSS Protection**: Input sanitization
- **CSRF Protection**: Token-based requests

## 🤝 Contributing

1. Follow the existing code structure
2. Use ES6+ features consistently
3. Maintain responsive design principles
4. Add proper error handling
5. Update documentation as needed

## 📄 License

This project is part of the Arsa Analiz ve Sunum Platformu and follows the same license terms.
