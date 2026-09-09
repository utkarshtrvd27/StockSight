# System Requirements
- Java Spring Boot >= 4.1.x
- Java >= 17 
- Maven >= 3.6.3 (Build Tools)
- Gradle >= 8.14 (Build Tools)
Refer to this documentation: https://docs.spring.io/spring-boot/installing.html

# Backend Features
1. Authentication and Authorization:
 - Stateless Authentication (JWT)
    - Issue JWT tokens after OTP verification for email-based login.
    - Tokens are used for API calls from the frontend.

 - Stateful Authentication (OAuth2)
    - Support Single Sign-On (SSO) with Google, GitHub, Instagram, etc.
    - Uses Spring Security OAuth2 client.

 - Role-Based Access Control (RBAC) for application features
    - Define roles (e.g., USER, ADMIN) and secure endpoints with @PreAuthorize.
    - Use Spring Data JDBC or JPA to store users_table, roles_table, permissions_table, users_roles_permissions table (join users_table, roles_table, and permissions_table)

2. Web APIs:
 - REST APIs for:
    - User operations (login, register, profile, etc.)
    - AI chatbot integration (LLM model endpoints)

3. Database connection:
 - Spring Data JDBC for PostgreSQL integration
 - (Optional) Spring Data JPA with Hibernate for advanced ORM features
 - Store user accounts, roles, sessions, and chatbot logs.

4. Distributed Session Management:
 - Spring Session for managing sessions across multiple servers
 - Useful if scaling horizontally (e.g., Kubernetes, cloud deployment)

5. AI Chatbot Integration:
 - LLM API Integration (Azure OpenAI / OpenAI / Hugging Face)
 - Spring Boot exposes /api/chat endpoint:
    - Receives user query from Next.js frontend
    - Calls external AI provider
    - Returns chatbot response
 - Streaming Support (optional)
    - Use WebSockets for real-time responses between server-client communication

6. Security Best Practices:
 - Use BCryptPasswordEncoder for password hashing
 - Configure HTTPS and secure headers
 - Store secrets in Azure Key Vault
 - Apply rate limiting for chatbot endpoints

7. Streaming Options:
 - WebSockets for real-time client-server communication
 - Apache Kafka (optional) for distributed event streaming and analytics

8. Deployment & Scalability:
 - Containerization with Docker
 - Orchestration with Kubernetes
 - Horizontal scaling supported via Spring Session and Kafka


# Method Writing style:
 - Use **camelCase**

# Class Writing style:
 - Use **PascalCase**

# API Testing Guidelines
1. Testing Framework:
 - Use JUnit 5 for unit and integration tests.
 - Use Spring Boot Test for context loading and dependency injection.
 - Use MockMvc for REST API endpoint testing.

2. Test Case Structure:
 - Follow **camelCase** for method names (e.g., `shouldReturnUserProfile`).
 - Group tests by feature (Authentication, User APIs, Chatbot APIs).
 - Use **PascalCase** for test classes (e.g., `AuthenticationControllerTest`).

3. Authentication Tests:
 - Verify JWT issuance after OTP verification.
 - Validate OAuth2 login flow with mock providers (Google, GitHub).
 - Ensure RBAC-secured endpoints reject unauthorized roles.

4. API Endpoint Tests:
 - Test success and failure scenarios for each endpoint.
 - Validate request/response payloads against expected schema.
 - Include edge cases (invalid input, missing headers, expired tokens).

5. Database Integration Tests:
 - Use Testcontainers for PostgreSQL to simulate real DB.
 - Ensure user, role, and permission mappings are persisted correctly.
 - Roll back transactions after each test to maintain isolation.

6. Chatbot Endpoint Tests:
 - Mock external LLM API calls (Azure OpenAI / Hugging Face).
 - Validate `/api/chat` returns structured responses.
 - Test WebSocket streaming for real-time communication.

7. Security Tests:
 - Verify password hashing with BCryptPasswordEncoder.
 - Ensure HTTPS and secure headers are enforced.
 - Test rate limiting on chatbot endpoints.

8. CI/CD Integration:
 - Run tests automatically via Maven/Gradle build pipeline.
 - Generate coverage reports (Jacoco).
 - Fail builds if coverage < 80%.