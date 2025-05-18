# Technical Context for CRM System

## Technology Stack
- **Backend Framework**: Flask (Python)
- **Database ORM**: SQLAlchemy
- **Frontend**: Bootstrap 5, JavaScript, Chart.js
- **Authentication**: Session-based authentication
- **Template Engine**: Jinja2

## Database Models
The CRM system uses the following key models:

1. **Contact**
   - Core fields: name, email, phone, role, status, source
   - Extended fields: address, city, country, social media, lead score
   - Relationships: belongs to User, belongs to Company, has many Interactions, Deals, Tasks

2. **Company**
   - Core fields: name, industry, website, address, phone
   - Extended fields: logo, employee count, revenue, social media
   - Relationships: belongs to User, has many Contacts, Deals

3. **Interaction**
   - Records communication with contacts
   - Fields: type, date, summary, outcome, next steps
   - Relationships: belongs to User, Contact, and optionally Deal

4. **Deal**
   - Represents sales opportunities
   - Fields: title, value, currency, stage, probability, dates
   - Relationships: belongs to User, Contact, Company, has Tasks, Interactions

5. **Task**
   - Represents to-do items
   - Fields: title, description, due date, status, priority
   - Relationships: belongs to User, can be assigned to User, linked to Contact/Deal

6. **Activity**
   - System logs for CRM actions
   - Fields: activity type, entity type, entity ID, description
   - Used for audit trail and activity feed

7. **CrmSettings**
   - User-specific CRM configuration
   - Fields: currency, date format, customizable status/stage options

## Architecture
- RESTful routes for CRUD operations
- Blueprint-based organization (crm.py)
- Server-side rendering with some AJAX functionality
- Authentication middleware for securing routes

## Current Limitations
- Limited reporting and analytics
- Basic UI with minimal customization
- No email integration
- Limited automation capabilities
- No mobile-specific optimizations