# AI Service

This service handles AI-powered chatbot and LLM integration for StockSight.

## Responsibilities
- Chatbot request handling
- Integration with external LLM providers such as OpenAI or Azure OpenAI
- Prompt orchestration and response formatting
- Optional streaming and WebSocket support
- AI usage logging and monitoring

## Tech Stack
- Java 17
- Spring Boot 4.1.x
- Spring Web
- Spring WebSocket
- Spring Data JDBC
- PostgreSQL

## Local development

```bash
mvn -pl ai-service spring-boot:run
```

## Notes
This module is separated from the REST API service so AI orchestration remains independent, easier to scale, and easier to evolve as provider integrations change.


## Troubleshooting Problems in the Terminal
- Project configuration is not up-to-date with pom.xml, requires an update => Open Command Palette and Run "Java: Reload Java Projects"
<b>Windows: Ctrl + Shift + P</b>

- Java project/classpath warning => Open Command Palette and Run "Java: Clean Java Language Server Workspace"
<b>Windows: Ctrl + Shift + P</b>