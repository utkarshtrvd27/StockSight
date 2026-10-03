# Auth Service

This service is responsible for user authentication and authorization in StockSight.

## Responsibilities
- User registration and login
- OTP-based email verification
- JWT token issuance and validation
- OAuth2 / SSO integration with providers such as Google and GitHub
- Role-based access control (RBAC)
- User, role, and permission management

## Implemented API

All endpoints are prefixed with `/api/v1/auth`:

- `POST /register`: creates a user with a BCrypt-hashed password and the default `USER` role.
- `POST /otp/request`: creates a short-lived OTP challenge for an existing email address.
- `POST /otp/verify`: validates the OTP once and returns a stateless JWT bearer token.
- `GET /me`: returns the authenticated user's profile and requires `Authorization: Bearer <token>`.

OTP codes are logged by `LoggingOtpSender` for local development only. Replace that bean with an email provider integration before deploying to a shared or production environment.

## Tech Stack
- Java 17
- Spring Boot 4.1.x
- Spring Security
- Spring Data JDBC
- PostgreSQL

## Local development

From the backend root:

```bash
mvn -pl auth-service -am spring-boot:run
```

The service listens on `http://localhost:8081`.

For PostgreSQL, set `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD`. Set `DB_INIT_MODE=always` for a local database where `schema.sql` should be applied automatically. Set a strong `AUTH_JWT_SECRET` with at least 32 bytes.

Run the focused tests with:

```bash
mvn -pl auth-service -am test
```

## Notes
This module is intentionally separated from the public REST API service so authentication concerns remain isolated and easier to secure and scale. OAuth2/SSO, external OTP delivery, persistent sessions, and fine-grained permissions are planned integration points; the current implementation uses stateless JWT authentication and the `USER`/`ADMIN` role claim foundation.
