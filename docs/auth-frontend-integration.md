# Auth API Integration Guide (Frontend)

This backend uses OTP login and returns a **pair of JWT tokens**:
- `access_token` (short-lived, for API calls)
- `refresh_token` (long-lived, for token renewal)

Base URL examples:
- Local: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

---

## 1) Request OTP

### Endpoint
`POST /auth/request-otp`

### Request body
```json
{
  "phone_number": "+1234567890"
}
```

### Success response (200)
```json
{
  "success": true,
  "data": {
    "message": "OTP sent successfully"
  },
  "error": null
}
```

### Error response (400)
```json
{
  "detail": "Failed to send OTP. Please try again."
}
```

> `firebase_token` is **NOT used** in this endpoint.

---

## 2) Verify OTP and Login

### Endpoint
`POST /auth/verify-otp`

### Request body (OTP flow)
```json
{
  "phone_number": "+1234567890",
  "code": "1234"
}
```

### Optional Firebase-assisted request body
```json
{
  "phone_number": "+1234567890",
  "code": "1234",
  "firebase_token": "<firebase-id-token>"
}
```

### Notes about `firebase_token`
- Field is optional.
- It is consumed **only** by `/auth/verify-otp`.
- If valid, backend can verify identity via Firebase path.
- If absent/invalid, backend falls back to Twilio OTP verification.

### Success response (200)
```json
{
  "success": true,
  "data": {
    "access_token": "<jwt-access-token>",
    "refresh_token": "<jwt-refresh-token>",
    "token_type": "bearer",
    "expires_in": 86400,
    "refresh_expires_in": 2592000
  },
  "error": null
}
```

### Error response (400)
```json
{
  "detail": "Invalid OTP code"
}
```

---

## 3) Refresh Tokens

### Endpoint
`POST /auth/refresh`

### Request body
```json
{
  "refresh_token": "<jwt-refresh-token>"
}
```

### Success response (200)
```json
{
  "success": true,
  "data": {
    "access_token": "<new-jwt-access-token>",
    "refresh_token": "<new-jwt-refresh-token>",
    "token_type": "bearer",
    "expires_in": 86400,
    "refresh_expires_in": 2592000
  },
  "error": null
}
```

### Error response (400)
```json
{
  "detail": "Invalid refresh token"
}
```

> Refresh tokens are rotated: each successful refresh returns a new access token and a new refresh token.

---

## 4) Use Access Token in Protected Requests

Set header:

`Authorization: Bearer <access_token>`

Example protected endpoint call:
- `POST /auth/select-role`

Request body:
```json
{
  "role": "freelancer"
}
```

---

## Frontend Integration Strategy (Recommended)

1. User enters phone -> call `/auth/request-otp`.
2. User enters OTP -> call `/auth/verify-otp`.
3. Save `access_token` + `refresh_token`.
4. Attach `access_token` in `Authorization` header for protected APIs.
5. On `401` (or just before expiry), call `/auth/refresh`.
6. Replace both tokens with returned pair.
7. If refresh fails (`400`), clear session and force re-login.

---

## Token Expiration Values

- `expires_in`: access token TTL in seconds.
- `refresh_expires_in`: refresh token TTL in seconds.

Use these values from backend response to schedule proactive refresh.

---

## Minimal Frontend Pseudocode

```ts
async function loginWithOtp(phone: string, code: string) {
  const res = await api.post('/auth/verify-otp', { phone_number: phone, code });
  const tokens = res.data.data;
  saveTokens(tokens.access_token, tokens.refresh_token, tokens.expires_in);
}

async function refreshSession() {
  const refreshToken = getRefreshToken();
  const res = await api.post('/auth/refresh', { refresh_token: refreshToken });
  const tokens = res.data.data;
  saveTokens(tokens.access_token, tokens.refresh_token, tokens.expires_in);
}
```

---

## Quick FAQ

### Why did I only get a small access token before?
Previously backend generated only one JWT with minimal claims and did not return refresh token. Now both tokens are returned and token claims include `type`, `iat`, and `jti`.

### Should frontend send `firebase_token` in `/auth/request-otp`?
No. `firebase_token` is optional and only belongs to `/auth/verify-otp`.
