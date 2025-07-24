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
- **2025-07-24**: Implemented dual integration architecture with ConnectWise PSA and CrewHu CSAT
- **2025-07-24**: Created comprehensive integration guides and setup wizards
- **2025-07-24**: Separated Support Satisfaction scoring to use CrewHu instead of ConnectWise resolution times
- **2025-07-01**: Fixed analytics dashboard layout, compressed client lists, moved stagnant accounts to AI trend analysis
- **2025-07-01**: Created realistic score data with wide variation (3-53 range) for meaningful chart visualization

## Key Features
- Multi-metric client scoring system (13 weighted metrics)
- AI-powered client categorization (At Risk, Stable, Stagnant)
- Real-time analytics dashboard with trend charts
- Role-based access control (ADMIN, MANAGER, VCIO, TAM)
- Comprehensive scoresheet management
- Export capabilities (PDF/Excel)

## Dual Integration Architecture (Completed)
**ConnectWise PSA + CrewHu CSAT Integration**
- ConnectWise handles operational metrics: tickets, time entries, agreements, first touch resolution
- CrewHu handles Support Engagement Satisfaction via CSAT scores
- Combined auto-scoring from both systems for comprehensive client engagement metrics
- Separate setup wizards and management interfaces for each integration
- Real-time webhook support and comprehensive documentation guides

## User Preferences
- Prioritize functional improvements over cosmetic changes
- Focus on practical business value and usability
- Maintain clean, professional interface design
- Ensure data accuracy and meaningful analytics