# PRD

## §3 User Stories

### US-001: Login
- AC: User can login with email/password
- AC: Failed login shows error
- AC: Lockout after 5 attempts

### US-002: Signup
- AC: New user creates account
- AC: Email verification sent

### US-003: Reset Password
- AC: Reset link sent to email

GET /api/login
POST /api/signup
POST /api/reset
