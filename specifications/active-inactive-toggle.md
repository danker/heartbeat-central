# Specification: Active/Inactive Toggle for Applications

## Overview
Add the ability to temporarily disable heartbeat monitoring for specific applications through both the web UI and API. This feature allows users to pause monitoring during maintenance windows, debugging sessions, or when an application is known to be offline, preventing unnecessary alerts while maintaining the application configuration.

## Requirements
### Functional Requirements
- Users can toggle monitoring on/off for individual applications via the web dashboard
- Toggle switch available on application cards for quick access
- Active/inactive state editable through the edit modal
- API support for updating the active/inactive state
- Inactive applications display "Monitoring Disabled" status in neutral gray
- No alerts are sent for inactive applications
- State changes are logged for audit purposes

### Non-Functional Requirements
- Performance: Toggle actions complete within 1 second
- Security: State changes require same permissions as application edits
- Compatibility: Works with existing alert plugins without modification
- UX: Clear visual distinction between inactive and problematic applications

## Technical Design
### Architecture
This feature leverages the existing `is_active` field in the Application model, which is already checked by the heartbeat monitor. The implementation focuses on exposing this field through the UI and API.

### Components
- **Frontend (dashboard.html)**: Add toggle switches and update status display logic
- **API (routes.py)**: Extend PUT endpoint to accept is_active field
- **Heartbeat Monitor**: No changes needed - already filters by is_active
- **Logging**: Add state change logging to application update logic

### Data Model
No database changes required. The `Application` model already has:
```python
is_active = db.Column(db.Boolean, default=True)
```

### API Design
**PUT /api/applications/{id}**
```json
{
  "name": "string (optional)",
  "expected_interval": "integer (optional)",
  "grace_period": "integer (optional)",
  "is_active": "boolean (optional)"
}
```

Response includes the updated application with `is_active` field.

## Implementation Details
### Files to Modify
- `templates/dashboard.html`: 
  - Add toggle switch to each application card
  - Update status badge logic to show "Monitoring Disabled" for inactive apps
  - Modify edit modal to include active/inactive checkbox
  - Add JavaScript functions for toggle handling

- `routes.py`:
  - Update PUT `/api/applications/{id}` endpoint to accept and validate `is_active` field
  - Add logging for state changes

- `static/css/style.css` (if exists) or inline styles:
  - Add styling for inactive application cards (subtle gray overlay or border)
  - Style the toggle switch component

### New Files
None required - all changes to existing files.

### Dependencies
No new dependencies needed. Will use:
- Bootstrap 5's built-in form-switch component for toggles
- Python's standard logging module for audit logs

## Testing Strategy
### Unit Tests
- Test API endpoint accepts is_active field and updates correctly
- Test API endpoint logs state changes
- Test API validation (is_active must be boolean)
- Verify to_dict() includes is_active field

### Integration Tests
- Test that inactive applications are excluded from heartbeat monitoring checks
- Test that setting inactive clears application from overdue set
- Test that reactivating an application resumes normal monitoring
- Verify no alerts sent for inactive applications

### Manual Testing
1. Create a test application
2. Let it become overdue
3. Toggle to inactive - verify status changes to "Monitoring Disabled"
4. Check logs for state change entry
5. Verify no alerts are sent
6. Toggle back to active - verify monitoring resumes
7. Test edit modal checkbox syncs with toggle switch

## Acceptance Criteria
- [ ] Toggle switch appears on each application card in the dashboard
- [ ] Toggle switch successfully enables/disables monitoring
- [ ] Inactive applications show "Monitoring Disabled" status in gray
- [ ] Edit modal includes "Active" checkbox that works correctly
- [ ] API PUT endpoint accepts is_active field and updates database
- [ ] State changes are logged with timestamp and application name
- [ ] Inactive applications do not trigger alerts
- [ ] Inactive applications do not appear in overdue checks
- [ ] Visual distinction clear between inactive and problematic apps
- [ ] All existing tests pass
- [ ] New tests added for toggle functionality

## Open Questions
- Should we add a "reason" field for why monitoring was disabled? (decided: no, just log for now)
- Should we show last known status alongside "Monitoring Disabled"? (decided: no, keep it simple)
- Should we add bulk enable/disable functionality? (future enhancement)

## References
- Existing is_active field: models.py:20
- Heartbeat monitor active filter: heartbeat_monitor.py:64
- Current dashboard template: templates/dashboard.html