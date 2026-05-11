```
PetPage (owner authenticated via Bearer token)
  ↓ clicks "Data Rights" / GDPR link
GdprPage /gdpr
  │
  ├─ GdprRequestForm
  │    Type selector (radio / dropdown):
  │      erasure | data_access | restrict_processing | object_leaderboard | rectification
  │    → POST /api/v1/gdpr/request  { type: "erasure" | ... }   (auth: Bearer token)
  │    ← { jobId, message }  HTTP 202 Accepted
  │    jobId stored in component state; GdprStatusBanner activates
  │
  ├─ GdprStatusBanner (after submission)
  │    Polls GET /api/v1/gdpr/request/status?jobId=<jobId>  (auth: Bearer token)
  │    Displays current status: pending | processing | completed | failed
  │    SLA copy displayed per request type:
  │      erasure → "Processed within 7 days (gdpr_email_deletion_window_days = 7)"
  │      data_access / portability → "Processed within 30 days (gdpr_data_access_response_days = 30; gdpr_data_portability_response_days = 30)"
  │      restrict_processing → "Processed within 24 hours (gdpr_restrict_processing_response_hours = 24)"
  │      object_leaderboard → "Processed within 5 business days (gdpr_object_leaderboard_response_business_days = 5)"
  │      rectification → "Processed within 24 hours (gdpr_email_rectification_response_hours = 24)"
  │
  └─ Error states:
       HTTP 400 VALIDATION_ERROR → inline form error: "Please select a valid request type."
       HTTP 401 → redirect to / (token cleared)
       HTTP 403 FORBIDDEN → "Your account is not authorized to view this request."
       HTTP 404 NOT_FOUND → "Request not found."
```