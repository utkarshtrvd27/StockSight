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

For PostgreSQL, set `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD`. Like the REST API service, this service imports an optional `.env` from its working directory or parent directory. Set `DB_INIT_MODE=always` there (or in the process environment) to apply `schema.sql` at startup; it creates the `auth` schema and the `auth.users_table` and `auth.otp_challenges` tables in the configured database. SQL initialization defaults to `never`. PostgreSQL schemas belong to a database, so inspect the same database configured by `DB_NAME`. Set a strong `AUTH_JWT_SECRET` with at least 32 bytes in `.env`; the application uses it as the JWT signing key and will not start without it.

OTP delivery uses SMTP outside the `dev` Spring profile. Configure `SMTP_HOST`, `SMTP_PORT` (default `587`), `SMTP_USERNAME`, `SMTP_PASSWORD`, and `OTP_FROM` in `.env`; SMTP authentication and STARTTLS are enabled by default and can be adjusted with `SMTP_AUTH`, `SMTP_STARTTLS_ENABLE`, and `SMTP_STARTTLS_REQUIRED`. The service fails to start outside `dev` if `SMTP_HOST` or `OTP_FROM` is missing. For local development without an email provider, start with the `dev` profile (`mvn spring-boot:run -Dspring-boot.run.profiles=dev`); that profile uses `LoggingOtpSender`, which logs OTPs and must never be enabled in production.

Run the focused tests with:

```bash
mvn -pl auth-service -am test
```

## Notes
This module is intentionally separated from the public REST API service so authentication concerns remain isolated and easier to secure and scale. OAuth2/SSO, external OTP delivery, persistent sessions, and fine-grained permissions are planned integration points; the current implementation uses stateless JWT authentication and the `USER`/`ADMIN` role claim foundation.


## Authentication and authorization flow

1. Registration normalizes the email address and stores a BCrypt-encoded password.
2. OTP requests generate a six-digit code using `SecureRandom`, store a BCrypt hash with an expiry and attempt count, and send the code through the configured `OtpSender`.
3. OTP verification checks expiry, consumption, attempt limits, and the stored hash. On success it consumes the challenge, marks the user's email verified, and issues a JWT.
4. The JWT service signs tokens using the configured `AUTH_JWT_SECRET`; the authentication filter validates the token and maps its signed role claim to a Spring Security authority.

`AUTH_JWT_SECRET` is a long-lived signing key shared by the issuer and verifier. It is not the JWT token itself and does not need to change for each token. Tokens are issued dynamically with their own claims and timestamps, and their signatures are computed using this configured key. Keep the key secret, high-entropy, and consistent across service instances that need to validate the same tokens.


## Troubleshooting Problems in the Terminal
- Project configuration is not up-to-date with pom.xml, requires an update => Open Command Palette and Run "Java: Reload Java Projects"
<b>Windows: Ctrl + Shift + P</b>

- Java project/classpath warning => Open Command Palette and Run "Java: Clean Java Language Server Workspace"
<b>Windows: Ctrl + Shift + P</b>