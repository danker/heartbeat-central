# Specification: Dashboard Templates Update

## Overview
Update the dashboard templates to display heartbeat-based application status instead of traditional healthcheck monitoring, providing clear visibility into application health and heartbeat patterns.

## Requirements
### Functional Requirements
- Display application heartbeat status with visual indicators
- Show last heartbeat timestamp and next expected heartbeat
- Provide heartbeat history visualization
- Display grace period and overdue status clearly
- Support real-time status updates

### Non-Functional Requirements
- Responsive design for mobile and desktop
- Page load time under 2 seconds
- Accessible UI following WCAG guidelines
- Browser compatibility (Chrome, Firefox, Safari, Edge)

## Technical Design
### Architecture
Update existing dashboard template structure to accommodate heartbeat-specific data while maintaining the current Flask templating approach.

### Components
- Main dashboard: Overview of all applications
- Application detail view: Individual application heartbeat history
- Status indicators: Visual representation of heartbeat health
- Real-time updates: WebSocket or polling for live status

### Data Model
Leverage existing Application and HeartbeatEvent models with additional computed properties:
```python
# Template context data structure
{
    'applications': [
        {
            'application': Application,
            'status': 'healthy|overdue|unknown',
            'last_heartbeat': datetime,
            'next_expected': datetime,
            'overdue_duration': timedelta,
            'recent_events': [HeartbeatEvent]
        }
    ]
}
```

### API Design
- GET /api/dashboard/data - JSON data for dashboard
- GET /api/applications/{id}/status - Real-time status for single app
- WebSocket /ws/status - Live status updates (future enhancement)

## Implementation Details
### Files to Modify
- `templates/dashboard.html`: Update main dashboard layout
- `templates/base.html`: Add common heartbeat-specific styles
- `routes.py`: Update dashboard route with new data structure
- `static/css/dashboard.css`: Heartbeat-specific styling
- `static/js/dashboard.js`: Real-time updates and interactions

### New Files
- `templates/partials/heartbeat_status.html`: Reusable status component
- `templates/application_detail.html`: Individual application view
- `static/css/heartbeat.css`: Heartbeat-specific styles

### Dependencies
- Chart.js or similar for heartbeat history visualization
- Moment.js for date/time formatting
- Bootstrap icons or similar for status indicators

## Testing Strategy
### Unit Tests
- Template rendering with various application states
- Data formatting and computation logic
- Status calculation accuracy

### Integration Tests
- Dashboard loads with multiple applications
- Real-time updates function correctly
- Mobile responsive layout

### Manual Testing
- Visual testing across different browsers
- Accessibility testing with screen readers
- Performance testing with large application lists

## Acceptance Criteria
- [ ] Dashboard clearly shows heartbeat status for all applications
- [ ] Overdue applications prominently highlighted
- [ ] Last heartbeat and next expected times displayed
- [ ] Responsive design works on mobile devices
- [ ] Page loads within 2 seconds with 100+ applications
- [ ] Real-time status updates without page refresh
- [ ] Accessible to users with disabilities

## Open Questions
- Should we implement WebSocket for real-time updates or use polling?
- What visualization format works best for heartbeat history?
- How should we handle timezone display for global deployments?

## References
- Current dashboard.html implementation
- Bootstrap documentation for responsive design
- WCAG accessibility guidelines
- Chart.js documentation for visualizations