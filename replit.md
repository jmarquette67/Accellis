# Accellis Client Engagement Platform

## Project Overview
An advanced organizational performance tracking platform that enables comprehensive multi-metric analysis and intelligent reporting for business performance evaluation.

**Current State**: Fully functional client engagement scoring system with AI-powered analytics

## Technical Stack
- **Backend**: Flask web framework with SQLModel/PostgreSQL
- **Frontend**: Bootstrap 5 with vanilla JavaScript
- **Authentication**: Local login system (admin@accellis.com / admin123)
- **Analytics**: AI-powered client risk assessment and trend analysis
- **Charts**: Chart.js for data visualization

## Recent Changes
- **2025-07-01**: Fixed analytics dashboard layout, compressed client lists, moved stagnant accounts to AI trend analysis
- **2025-07-01**: Created realistic score data with wide variation (3-53 range) for meaningful chart visualization
- **2025-07-01**: Implemented clickable client names with AI analysis modals for At Risk, Stable, and Stagnant clients

## Key Features
- Multi-metric client scoring system (13 weighted metrics)
- AI-powered client categorization (At Risk, Stable, Stagnant)
- Real-time analytics dashboard with trend charts
- Role-based access control (ADMIN, MANAGER, VCIO, TAM)
- Comprehensive scoresheet management
- Export capabilities (PDF/Excel)

## Integration Requirements
**ConnectWise Integration Planning** (New Request)
- Need to sync client data, tickets, and metrics with ConnectWise
- Potential API endpoints for data exchange
- Authentication and security considerations
- Data mapping between systems

## User Preferences
- Prioritize functional improvements over cosmetic changes
- Focus on practical business value and usability
- Maintain clean, professional interface design
- Ensure data accuracy and meaningful analytics