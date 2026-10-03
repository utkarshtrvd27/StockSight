# REST API Service

This module exposes the public REST API for StockSight. It is the frontend-facing backend service responsible for stock market data, search, and pipeline health endpoints.

## Purpose

The REST API service is designed to:
- serve market overview and stock data to the frontend
- expose search and detail endpoints for stock lookup
- return historical time-series data for charting
- report the current health of the ETL pipeline and database connectivity

This module sits in the multi-service backend layout alongside the authentication and AI services.

## Requirements

- Java 17+
- Maven 3.6.3+
- PostgreSQL populated by the ETL pipeline
- Spring Boot 4.1.x

## Local setup

From this module directory, run:

```powershell
mvn spring-boot:run
```

Local database settings are loaded from `stocksight_backend/.env` when starting from this module directory. Environment variables supplied by the shell or deployment environment take precedence.

The service listens on:

```text
http://localhost:8080
```

To run only the REST API tests:

```powershell
mvn test
```

## API endpoints

### Market

#### `GET /api/v1/market/overview`
Returns a market summary including:
- tracked stock count
- latest trading date
- top gainers
- top losers
- average PnL percentage

#### `GET /api/v1/market/gainers`
Returns the top gainers for the latest trading date.
Supports the optional query parameter `limit` with a default value of `20`.

#### `GET /api/v1/market/losers`
Returns the top losers for the latest trading date.
Supports the optional query parameter `limit` with a default value of `20`.

### Stocks

#### `GET /api/v1/stocks/search`
Returns lightweight stock search suggestions for autocomplete and type-ahead behavior.
Supports:
- `query` (optional)  <!-- Add "query" parameter in Postman -->
- `limit` (default `10`)

#### `GET /api/v1/stocks/{stockCode}`
Returns the latest summary for a specific stock, including:
- stock code
- stock name
- ISIN
- last trading date
- closing price
- PnL percentage
- average PnL percentage

### Historical data

#### `GET /api/v1/stocks/history/{stockCode}`
Returns historical stock price information for a given stock.
Supports optional query parameters:
- `from` (ISO date)
- `to` (ISO date)
- `limit` (default `14`)

This endpoint is intended for charting and trend analysis.

### Pipeline status

#### `GET /api/v1/pipeline/status`
Checks whether the ETL pipeline and underlying data layer are healthy.

It verifies:
- database connectivity
- whether the gold table is available
- latest business date availability

Returns:
- HTTP `200` when healthy
- HTTP `503` when the database is unavailable

## Notes

- This module is intentionally read-only and public-facing.
- It is separated from the authentication and AI services to keep the service boundaries clear.
- The REST layer remains a thin API surface over the market data and pipeline status sources.
- Tests are implemented with `MockMvc`, so HTTP behavior can be validated without requiring a live PostgreSQL instance.



## Troubleshooting Problems in the Terminal
- Project configuration is not up-to-date with pom.xml, requires an update => Open Command Palette and Run "Java: Reload Java Projects"
<b>Windows: Ctrl + Shift + P</b>

- Java project/classpath warning => Open Command Palette and Run "Java: Clean Java Language Server Workspace"
<b>Windows: Ctrl + Shift + P</b>