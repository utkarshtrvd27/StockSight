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
- `GET /me`: returns the authenticated user's profile and requires a bearer token in the `Authorization` header.

OTP codes are delivered by SMTP except when the `dev` Spring profile is active. The development-only `LoggingOtpSender` writes recipient addresses and OTP codes to application logs; never enable that profile in a shared or production environment.

## Tech Stack

- Java 17
- Spring Boot 4.1.x
- Spring Security
- Spring Data JDBC
- PostgreSQL

## Local development

Run commands from the `stocksight_backend` root.

Start the service:

```bash
mvn -pl auth-service -am spring-boot:run
```

The service listens on `http://localhost:8081`.

The service imports an optional `.env` from its working directory or parent directory. Configure PostgreSQL with `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD`. Set `DB_INIT_MODE=always` to apply `schema.sql` at startup and create the `auth` schema, `auth.users_table`, and `auth.otp_challenges` in the configured database. Initialization defaults to `never`; PostgreSQL schemas belong to a database, so inspect the database selected by `DB_NAME`.

Set a strong, high-entropy `AUTH_JWT_SECRET` of at least 32 bytes. This is the key used to sign and verify dynamically issued JWTs; it is not a per-token value. Keep it out of source control.

### SMTP configuration

SMTP delivery is used whenever the `dev` profile is not active. Configure these variables in `.env` or the process environment:

| Variable | Required | Default | Description |
|---|---:|---|---|
| `SMTP_HOST` | Yes | — | SMTP server hostname |
| `SMTP_PORT` | No | `587` | SMTP server port |
| `SMTP_USERNAME` | Provider-dependent | Empty | SMTP account username |
| `SMTP_PASSWORD` | Provider-dependent | Empty | SMTP account password or app password |
| `OTP_FROM` | Yes | — | Sender address authorized by the SMTP provider |
| `SMTP_AUTH` | No | `true` | Enable SMTP authentication |
| `SMTP_STARTTLS_ENABLE` | No | `true` | Enable STARTTLS |
| `SMTP_STARTTLS_REQUIRED` | No | `true` | Require STARTTLS |

The service fails to start outside `dev` when `SMTP_HOST` or `OTP_FROM` is missing. SMTP authentication and STARTTLS are enabled by default. Docker Compose requires `AUTH_JWT_SECRET`, `SMTP_HOST`, and `OTP_FROM` in the backend `.env` and forwards the SMTP settings to the auth service. Never commit secrets to source control.

For local development without an SMTP provider, activate the `dev` profile from the backend root:

```bash
mvn -pl auth-service -am spring-boot:run -Dspring-boot.run.profiles=dev
```

This profile uses `LoggingOtpSender`, which logs OTP values. Use it only on a trusted local development machine.

Run the focused tests from the backend root:

```bash
mvn -pl auth-service -am test
```

## Authentication and authorization flow

1. Registration normalizes the email address and stores a BCrypt-encoded password.
2. OTP requests generate a six-digit code using `SecureRandom`, store a BCrypt hash with an expiry and attempt count, and send the code through the configured `OtpSender`.
3. OTP verification checks expiry, consumption, attempt limits, and the stored hash. On success it consumes the challenge, marks the user's email verified, and issues a JWT.
4. The JWT service signs tokens using `AUTH_JWT_SECRET`; the authentication filter validates the token and maps its signed role claim to a Spring Security authority.

`AUTH_JWT_SECRET` is a long-lived signing key shared by the issuer and verifier. Each JWT is issued dynamically with its own claims and timestamps, and its signature is computed using this configured key. Keep the key secret, high-entropy, and consistent across service instances that need to validate the same tokens.

## Notes

This module is intentionally separated from the public REST API service so authentication concerns remain isolated and easier to secure and scale. OAuth2/SSO, persistent sessions, and fine-grained permissions are planned integration points; the current implementation uses SMTP-backed OTP verification, stateless JWT authentication, and the `USER`/`ADMIN` role claim foundation.

## Troubleshooting Problems in the Terminal

- Project configuration is not up-to-date with pom.xml, requires an update: open the Command Palette and run `Java: Reload Java Projects`.
  - Windows: `Ctrl + Shift + P`
- Java project/classpath warning: open the Command Palette and run `Java: Clean Java Language Server Workspace`.
  - Windows: `Ctrl + Shift + P`
