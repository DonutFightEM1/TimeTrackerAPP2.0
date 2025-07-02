# TimeTracker Pro - System Architecture

## Overview

TimeTracker Pro is a comprehensive employee time tracking application built with Flask. It provides time clock functionality with GPS location tracking, paid time off (PTO) management, and administrative oversight capabilities. The system is designed for businesses that need to track employee work hours with location verification and manage time-off requests.

## System Architecture

### Backend Architecture
- **Framework**: Flask 3.1.1 with Python 3.11
- **ORM**: SQLAlchemy 2.0.41 with Flask-SQLAlchemy
- **Authentication**: Flask-Login for session management
- **Database**: SQLite for development, PostgreSQL ready for production
- **WSGI Server**: Gunicorn for production deployment

### Frontend Architecture
- **Template Engine**: Jinja2 (Flask's built-in templating)
- **CSS Framework**: Bootstrap 5.3.0
- **Icons**: Font Awesome 6.4.0
- **Typography**: Google Fonts (Inter)
- **JavaScript**: Vanilla JS with GPS/location services integration

### Database Schema
The application uses SQLAlchemy models with the following core entities:

- **User**: Employee accounts with role-based access (employee/manager)
- **TimeEntry**: Clock in/out records with GPS coordinates and location data
- **PTORequest**: Paid time off requests with approval workflow
- **Company**: Organization settings (referenced but not fully implemented)

## Key Components

### Authentication System
- User registration and login with password hashing (Werkzeug)
- Role-based access control (employee vs manager)
- Session management with Flask-Login
- Protected routes requiring authentication

### Time Tracking Core
- GPS-enabled clock in/out functionality
- Location validation and reverse geocoding
- Real-time status tracking (clocked in/out)
- Time calculation and hour summaries
- Approval workflow for time entries

### PTO Management
- Employee PTO balance tracking
- Request submission system
- Manager approval workflow
- Multiple PTO types (vacation, sick, personal)

### Administrative Dashboard
- Manager oversight of employee time entries
- Bulk approval/rejection capabilities
- Employee management interface
- Reporting and analytics (basic implementation)

## Data Flow

### Clock In/Out Process
1. User accesses dashboard
2. GPS location is requested and validated
3. Location coordinates and address are captured
4. Time entry is created with timestamp and location data
5. Status is updated in real-time
6. Entry awaits manager approval

### PTO Request Flow
1. Employee submits PTO request with dates and type
2. System validates against available PTO balance
3. Request enters pending status
4. Manager reviews and approves/rejects
5. PTO balance is updated upon approval
6. Employee receives notification of decision

### Administrative Workflow
1. Manager accesses admin dashboard
2. Pending items are displayed (time entries, PTO requests)
3. Bulk actions available for efficiency
4. Approval decisions are logged with timestamps
5. Employees can view updated statuses

## External Dependencies

### Required Python Packages
- Flask ecosystem (Flask, Flask-SQLAlchemy, Flask-Login)
- Database drivers (psycopg2-binary for PostgreSQL)
- Email validation (email-validator with dnspython)
- Production server (Gunicorn)
- Security utilities (Werkzeug)

### Frontend Dependencies
- Bootstrap 5.3.0 (CSS framework)
- Font Awesome 6.4.0 (icons)
- Google Fonts API (Inter font family)

### Browser APIs
- Geolocation API for GPS functionality
- Local storage for caching location data
- Notification API for status updates

## Deployment Strategy

### Development Environment
- SQLite database for local development
- Flask development server with auto-reload
- Debug mode enabled for development
- Environment variables for configuration

### Production Environment
- Gunicorn WSGI server with autoscaling deployment
- PostgreSQL database with connection pooling
- Environment-based configuration management
- ProxyFix middleware for proper header handling
- SSL/HTTPS termination at load balancer level

### Deployment Configuration
- Replit-based deployment with Nix package management
- Automatic scaling based on demand
- Health checks on port 5000
- Session secret management via environment variables

The application is containerized and ready for cloud deployment with minimal configuration changes required for different environments.

## Recent Changes

- June 24, 2025: Added employee directory with admin management capabilities
- June 24, 2025: Implemented promote/demote functionality for user roles
- June 24, 2025: Added user deletion capability with safety checks
- June 24, 2025: Restricted breaks to one per clock-in cycle
- June 24, 2025: Added clock-out confirmation dialog
- June 25, 2025: Enhanced GPS-optional functionality - employees can clock in/out without location
- June 25, 2025: Added automatic admin review flagging for entries without GPS coordinates
- June 25, 2025: Implemented location unavailable warnings and status indicators
- June 24, 2025: Moved time clock to top of dashboard for better accessibility
- June 24, 2025: Added Break functionality with 30-minute default timer
- June 24, 2025: Updated PTO system to support UTO (Unpaid Time Off) and PTO options
- June 24, 2025: Implemented break notifications (5-minute warning and end-of-break alerts)
- June 24, 2025: Enhanced time tracking to exclude break time from total hours worked
- June 24, 2025: Initial setup and core functionality deployment

## Changelog

Changelog:
- June 24, 2025. Initial setup
- June 24, 2025. Added break management and UTO/PTO selection

## User Preferences

Preferred communication style: Simple, everyday language.