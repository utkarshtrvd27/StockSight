package com.stocksight.rest.stock;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

public final class StockModels {
    private StockModels() {
    }

    public record StockSearchResult(String stockCode, String stockName, String isin) {
    }

    public record StockSummary(String stockCode, String stockName, String isin, LocalDate businessDate,
                               BigDecimal closingPrice, BigDecimal pnlPercentage, BigDecimal averagePnlPercentage) {
    }

    public record StockPrice(LocalDate businessDate, BigDecimal openPrice, BigDecimal highPrice,
                             BigDecimal lowPrice, BigDecimal closingPrice, BigDecimal lastPrice,
                             BigDecimal previousClosingPrice, BigDecimal pnlPercentage, Long totalTradingVolume) {
    }

    public record StockIndicator(LocalDate businessDate, BigDecimal closingPrice, BigDecimal ema7) {
    }

    public record StockDetails(StockSummary latest, List<StockPrice> history, List<StockIndicator> indicators) {
    }

    public record MarketOverview(LocalDate latestBusinessDate, long trackedStocks,
                                 BigDecimal averagePnlPercentage, List<StockSummary> gainers,
                                 List<StockSummary> losers) {
    }

    public record PipelineStatus(boolean databaseReachable, boolean goldTableAvailable,
                                 LocalDate latestBusinessDate) {
    }
}