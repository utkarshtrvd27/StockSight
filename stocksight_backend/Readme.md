# StockSight Backend

This repository contains the backend services for StockSight, organized as a multi-module Spring Boot project.

## Architecture overview

The backend is divided into separate service modules so each concern has a clear boundary:

- `rest-api-service`: public REST API for frontend clients and market data access
- `auth-service`: authentication, authorization, JWT/OAuth2, and user management
- `ai-service`: AI chatbot and LLM integration
- `shared-lib`: common DTOs and reusable shared code

This modular separation helps keep the codebase easier to understand, test, and scale as the platform grows.

## Project structure

```text
stocksight_backend/
├── pom.xml
├── Readme.md
├── .github/
├── docker-compose.yml
├── shared-lib/
│   ├── pom.xml
│   └── src/
├── auth-service/
│   ├── README.md
│   ├── pom.xml
│   ├── Dockerfile
│   └── src/
├── ai-service/
│   ├── README.md
│   ├── pom.xml
│   ├── Dockerfile
│   └── src/
├── rest-api-service/
│   ├── Readme.md
│   ├── pom.xml
│   ├── Dockerfile
│   └── src/
└── .env
```

## Module responsibilities

### REST API service
The public-facing API service for StockSight.

Responsibilities:
- stock search and lookup endpoints
- market overview and gainers/losers data
- historical stock data for charts
- pipeline health checks
- REST integration with the frontend

See: [rest-api-service/Readme.md](rest-api-service/Readme.md)

### Auth service
Authentication and authorization service.

Responsibilities:
- user registration and login
- OTP verification flow
- JWT generation and validation
- OAuth2 / SSO
- RBAC and permission enforcement

See: [auth-service/README.md](auth-service/README.md)

### AI service
AI and chatbot integration service.

Responsibilities:
- LLM provider integration
- chat request handling
- prompt processing
- optional streaming/WebSocket support
- AI request logging and monitoring

See: [ai-service/README.md](ai-service/README.md)

### Shared library
Common shared code used across modules.

Responsibilities:
- shared DTOs
- reusable utility classes
- common constants and models

## Build and run

From the root folder:

```bash
mvn clean install
```

Run each service individually:

```bash
mvn -pl rest-api-service spring-boot:run
mvn -pl auth-service spring-boot:run
mvn -pl ai-service spring-boot:run
```

Or run the dockerized setup:

```bash
docker-compose up --build
```

## Local ports

- REST API service: http://localhost:8080
- Auth service: http://localhost:8081
- AI service: http://localhost:8082

## Development notes

- The current implementation already contains the REST stock API and is treated as the public backend layer.
- Auth service now provides the initial user authentication slice: registration, OTP challenge verification, BCrypt password hashing, JWT issuance, and authenticated profile access. AI remains scaffolded and ready for expansion according to the project requirements.
- This structure makes it easier to manage service ownership, deployments, and future scaling.

## Repository conventions

- Java 17+
- Spring Boot 4.1.x
- Maven multi-module build
- Feature separation by responsibility, not by package only
- README files kept per module for service-specific documentation


## Troubleshooting Problems in the Terminal
- Project configuration is not up-to-date with pom.xml, requires an update => Open Command Palette and Run "Java: Reload Java Projects"
<b>Windows: Ctrl + Shift + P</b>

- Java project/classpath warning => Open Command Palette and Run "Java: Clean Java Language Server Workspace"
<b>Windows: Ctrl + Shift + P</b>