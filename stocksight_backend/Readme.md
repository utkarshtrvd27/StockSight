# StockSight Backend

Spring Boot read-only API for the StockSight PostgreSQL Gold layer.

## Requirements

- Java 17+
- Maven 3.6.3+
- PostgreSQL populated by `stocksight_ETL`

## Local setup

1. Set the local PostgreSQL password in the environment used by the Spring Boot app.
2. Ensure the ETL pipeline has created the `gold.indianstocks` table.
3. Start the API from this directory:

```powershell
mvn spring-boot:run
```

The API listens on `http://localhost:8080`.

To run the API tests without starting the server:

```powershell
mvn test
```

The endpoint tests use `MockMvc` with a mocked service, so they validate HTTP routes, parameters, response JSON, and status codes without requiring a running PostgreSQL instance. The application itself still requires PostgreSQL when started with `mvn spring-boot:run`.

## API endpoints

### 1. Market

#### `GET /api/v1/market/overview`
Returns the market snapshot with:
- total number of stocks
- latest trading date
- top movers based on average PnL percentage
- top losers based on average PnL percentage

#### `GET /api/v1/market/gainers`
Returns the top gainers for the latest trading date. Supports an optional `limit` query parameter, defaulting to 10.

#### `GET /api/v1/market/losers`
Returns the top losers for the latest trading date. Supports an optional `limit` query parameter, defaulting to 10.

### 2. Stocks

#### `GET /api/v1/stocks/{stockCode}`
Returns the stock summary for a given stock code, including:
- stock name
- ISIN number
- last trading date
- closing price
- PnL percentage
- average PnL percentage

#### `GET /api/v1/stocks/search`
Internal autocomplete/search endpoint for stock lookup. Intended for dropdown and type-ahead behavior.

### 3. Historical Data

#### `GET /api/v1/stocks/history/{stockCode}`
Returns historical data for the selected stock, filtered by optional `from`, `to`, and `limit` parameters. Default `limit` is 14.

The historical response contains time-series stock price and volume information intended for charting and trend analysis.

### 4. Pipeline Status

#### `GET /api/v1/pipeline/status`
Checks whether the pipeline is healthy by verifying:
- database reachability
- `gold.indianstocks` table existence
- latest business date availability

Returns HTTP `200` when healthy and `503` when the database is unreachable.

## Notes

This backend is intentionally read-only and local. It is designed to serve market overview, stock summaries, historical time series, and pipeline health data for the front-end and ETL monitoring workflows.