package com.stocksight.backend.stock;

import com.stocksight.backend.stock.StockModels.MarketOverview;
import com.stocksight.backend.stock.StockModels.PipelineStatus;
import com.stocksight.backend.stock.StockModels.StockDetails;
import com.stocksight.backend.stock.StockModels.StockSearchResult;
import com.stocksight.backend.stock.StockModels.StockSummary;
import org.springframework.jdbc.CannotGetJdbcConnectionException;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

@Service
public class StockService {
    private static final int DEFAULT_LIMIT = 20;
    private static final int MAX_LIMIT = 100;
    private static final int SEARCH_LIMIT = 20;

    private final StockRepository repository;
    private final StockSearchCatalog searchCatalog;

    public StockService(StockRepository repository, StockSearchCatalog searchCatalog) {
        this.repository = repository;
        this.searchCatalog = searchCatalog;
    }

    public List<StockSearchResult> searchSuggestions(String query, int limit) {
        return searchCatalog.search(query, Math.min(boundedLimit(limit), SEARCH_LIMIT));
    }

    public List<StockSummary> search(String query, int limit) {
        return repository.search(query, boundedLimit(limit));
    }

    public StockSummary latest(String stockCode) {
        return repository.findLatest(stockCode).orElseThrow(() -> new StockNotFoundException(stockCode));
    }

    public StockDetails details(String stockCode, LocalDate from, LocalDate to, int limit) {
        if (from != null && to != null && from.isAfter(to)) {
            throw new IllegalArgumentException("from must be before or equal to to");
        }
        return new StockDetails(
                repository.findLatest(stockCode).orElseThrow(() -> new StockNotFoundException(stockCode)),
                repository.history(stockCode, from, to, boundedLimit(limit)),
                repository.indicators(stockCode, boundedLimit(limit))
        );
    }

    public List<com.stocksight.backend.stock.StockModels.StockPrice> history(
            String stockCode, LocalDate from, LocalDate to, int limit) {
        if (from != null && to != null && from.isAfter(to)) {
            throw new IllegalArgumentException("from must be before or equal to to");
        }
        return repository.history(stockCode, from, to, boundedLimit(limit));
    }

    public List<com.stocksight.backend.stock.StockModels.StockIndicator> indicators(String stockCode, int limit) {
        return repository.indicators(stockCode, boundedLimit(limit));
    }

    public List<StockSummary> movers(boolean gainers, int limit) {
        return repository.movers(gainers, boundedLimit(limit));
    }

    public MarketOverview overview() {  // Done
        List<StockSummary> gainers = repository.movers(true, 5);
        List<StockSummary> losers = repository.movers(false, 5);
        BigDecimal average = repository.averagePnlPercentage();
        return new MarketOverview(repository.latestBusinessDate(), repository.trackedStocks(),
            average == null ? BigDecimal.ZERO : average, gainers, losers);
    }

    public PipelineStatus pipelineStatus() {
        try {
            boolean available = repository.goldTableAvailable();
            return new PipelineStatus(true, available, available ? repository.latestBusinessDate() : null);
        } catch (CannotGetJdbcConnectionException exception) {
            return new PipelineStatus(false, false, null);
        }
    }

    private int boundedLimit(int requested) {
        return requested <= 0 ? DEFAULT_LIMIT : Math.min(requested, MAX_LIMIT);
    }

    public static class StockNotFoundException extends RuntimeException {
        public StockNotFoundException(String stockCode) {
            super("Stock not found: " + stockCode);
        }
    }
}