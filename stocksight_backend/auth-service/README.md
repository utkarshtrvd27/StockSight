# Auth Service

This service is responsible for authentication and authorization in StockSight.

## Responsibilities
- User registration and login
- OTP-based email verification
- JWT token issuance and validation
- OAuth2 / SSO integration with providers such as Google and GitHub
- Role-based access control (RBAC)
- User, role, and permission management

## Tech Stack
- Java 17
- Spring Boot 4.1.x
- Spring Security
- Spring Data JDBC
- PostgreSQL

## Local development

```bash
mvn -pl auth-service spring-boot:run
```

## Notes
This module is intentionally separated from the public REST API service so authentication concerns remain isolated and easier to secure and scale.
