# Authentication and Authorization Security Review

**Scope:** `stocksight_backend/auth-service`  
**Review date:** 2026-10-04

## Summary

The review found no confirmed exploitable vulnerabilities in the reviewed authentication and authorization flow. It identified one high-severity concern that depends on deployment configuration: the current OTP sender logs live one-time codes and email addresses in plaintext.

| # | Severity | File | Lines | Finding | Confidence |
|---|----------|------|-------|---------|------------|
| 1 | 🟠 HIGH | `stocksight_backend/auth-service/src/main/java/com/stocksight/auth/auth/LoggingOtpSender.java` | 7-14 | The OTP sender is an unconditional Spring component that logs the recipient email and OTP in plaintext. If used in production and logs are accessible to an attacker or unauthorized operator while the code is valid, the code and challenge ID can be used to verify the challenge and obtain a bearer token. Replace it with a real delivery provider or restrict it to an explicit development profile, and protect any retained logs. | 8/10 |

This finding is conditional on the deployed bean and access to its logs; no evidence from this code review establishes that a production deployment is exposed.

## Authentication and authorization flow

1. Registration normalizes the email address and stores a BCrypt-encoded password.
2. OTP requests generate a six-digit code using `SecureRandom`, store a BCrypt hash with an expiry and attempt count, and send the code through the configured `OtpSender`.
3. OTP verification checks expiry, consumption, attempt limits, and the stored hash. On success it consumes the challenge, marks the user's email verified, and issues a JWT.
4. The JWT service signs tokens using the configured `AUTH_JWT_SECRET`; the authentication filter validates the token and maps its signed role claim to a Spring Security authority.

`AUTH_JWT_SECRET` is a long-lived signing key shared by the issuer and verifier. It is not the JWT token itself and does not need to change for each token. Tokens are issued dynamically with their own claims and timestamps, and their signatures are computed using this configured key. Keep the key secret, high-entropy, and consistent across service instances that need to validate the same tokens.

## Deployment configuration note

The repository's Docker Compose auth-service environment does not declare `AUTH_JWT_SECRET`. Unless it is supplied through another deployment mechanism, the service will not start with the required JWT configuration. Inject a strong secret through the deployment environment or a secret manager; do not commit it to source control.
