# Authentication and Authorization Security Review

**Scope:** `stocksight_backend/auth-service`  
**Review date:** 2026-10-04

## Summary

The review found no confirmed exploitable vulnerabilities in the reviewed authentication and authorization flow. It identified a high-severity concern in the original implementation: the OTP sender logged live one-time codes and email addresses in plaintext. **Status: addressed** by restricting that sender to the explicit `dev` Spring profile and using SMTP outside that profile.

| # | Severity | File | Lines | Finding | Confidence | Status |
|---|----------|------|-------|---------|------------|--------|
| 1 | 🟠 HIGH | `stocksight_backend/auth-service/src/main/java/com/stocksight/auth/auth/LoggingOtpSender.java` | 7-14 | The original unconditional OTP sender logged the recipient email and live OTP in plaintext. If used in production with accessible logs, an attacker could use the OTP and challenge ID to obtain a bearer token. | 8/10 | Addressed: restricted to `dev`; SMTP sender is used otherwise. |

The original exposure depended on deployment and log access; no evidence established that a production deployment was exposed.

## Authentication and authorization flow

1. Registration normalizes the email address and stores a BCrypt-encoded password.
2. OTP requests generate a six-digit code using `SecureRandom`, store a BCrypt hash with an expiry and attempt count, and send the code through the configured `OtpSender`.
3. OTP verification checks expiry, consumption, attempt limits, and the stored hash. On success it consumes the challenge, marks the user's email verified, and issues a JWT.
4. The JWT service signs tokens using the configured `AUTH_JWT_SECRET`; the authentication filter validates the token and maps its signed role claim to a Spring Security authority.

`AUTH_JWT_SECRET` is a long-lived signing key shared by the issuer and verifier. It is not the JWT token itself and does not need to change for each token. Tokens are issued dynamically with their own claims and timestamps, and their signatures are computed using this configured key. Keep the key secret, high-entropy, and consistent across service instances that need to validate the same tokens.

## Deployment configuration note

Docker Compose now requires `AUTH_JWT_SECRET`, `SMTP_HOST`, and `OTP_FROM` through the backend `.env` file and forwards them to the auth service. Supply real SMTP settings and a strong JWT signing key; do not commit secrets to source control.
