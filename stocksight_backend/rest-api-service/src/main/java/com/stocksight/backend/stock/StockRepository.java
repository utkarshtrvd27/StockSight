package com.stocksight.backend.stock;

import com.stocksight.backend.stock.StockModels.StockIndicator;
import com.stocksight.backend.stock.StockModels.StockPrice;
import com.stocksight.backend.stock.StockModels.StockSearchResult;
import com.stocksight.backend.stock.StockModels.StockSummary;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

@Repository
public class StockRepository {
    private final JdbcTemplate jdbcTemplate;

    public StockRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public List<StockSearchResult> stockCatalog() {
        return jdbcTemplate.query("""
                SELECT DISTINCT ON (stock_code) stock_code, stock_name, "ISIN" AS isin
                FROM gold.indianstocks
                WHERE stock_code IS NOT NULL
                ORDER BY stock_code, business_date DESC
                """, (rs, rowNum) -> new StockSearchResult(rs.getString("stock_code"), rs.getString("stock_name"), rs.getString("isin")
                )
        );
    }

    public List<StockSummary> search(String search, int limit) {
        String pattern = search == null || search.isBlank() ? "%" : "%" + search.trim().toUpperCase() + "%";
        return jdbcTemplate.query("""
                SELECT DISTINCT ON (stock_code) stock_code, stock_name, "ISIN" AS isin, business_date,
                       closing_price, pnl_percentage, avg_pnl_percentage
                FROM gold.indianstocks
                WHERE UPPER(COALESCE(stock_name, '')) LIKE ?
                ORDER BY stock_code, business_date DESC
                LIMIT ?
                """, summaryMapper(), pattern, limit);
    }

    public Optional<StockSummary> findLatest(String stockCode) {
        List<StockSummary> rows = jdbcTemplate.query("""
                SELECT stock_code, stock_name, "ISIN" AS isin, business_date,
                       closing_price, pnl_percentage, avg_pnl_percentage
                FROM gold.indianstocks
                WHERE UPPER(stock_code) = UPPER(?)
                ORDER BY business_date DESC LIMIT 1
                """, summaryMapper(), stockCode);
        return rows.stream().findFirst();
    }

    public List<StockPrice> history(String stockCode, LocalDate from, LocalDate to, int limit) {
        return jdbcTemplate.query("""
                SELECT business_date, open_price, high_price, low_price, closing_price, last_price,
                       previous_closing_price, pnl_percentage, total_trading_volume
                FROM gold.indianstocks
                WHERE UPPER(stock_code) = UPPER(?)
                  AND (? IS NULL OR business_date >= ?)
                  AND (? IS NULL OR business_date <= ?)
                ORDER BY business_date DESC LIMIT ?
                """, (rs, rowNum) -> new StockPrice(
                rs.getObject("business_date", LocalDate.class), rs.getBigDecimal("open_price"),
                rs.getBigDecimal("high_price"), rs.getBigDecimal("low_price"),
                rs.getBigDecimal("closing_price"), rs.getBigDecimal("last_price"),
                rs.getBigDecimal("previous_closing_price"), rs.getBigDecimal("pnl_percentage"),
                rs.getObject("total_trading_volume", Long.class)
        ), stockCode, from, from, to, to, limit);
    }

    public List<StockIndicator> indicators(String stockCode, int limit) {
        return jdbcTemplate.query("""
                SELECT g.business_date, g.closing_price, e.ema_7
                FROM gold.indianstocks g
                LEFT JOIN silver.indianstocks_ema e ON e.hash_key = g.hash_key
                WHERE UPPER(g.stock_code) = UPPER(?)
                ORDER BY g.business_date DESC LIMIT ?
                """, (rs, rowNum) -> new StockIndicator(
                rs.getObject("business_date", LocalDate.class), rs.getBigDecimal("closing_price"),
                rs.getBigDecimal("ema_7")
        ), stockCode, limit);
    }

    public List<StockSummary> movers(boolean gainers, int limit) {
        String direction = gainers ? "DESC" : "ASC";
        String sql = """
                    SELECT "ISIN", stock_code, stock_name , business_date,
                            SUM(open_price) as open_price,
                            SUM(closing_price) as closing_price, 
                            SUM(previous_closing_price) as previous_closing_price,
                            SUM(total_trading_volume) as total_trading_volume,
                            SUM(pnl_percentage) as pnl_percentage, 
                            SUM(avg_pnl_percentage) as avg_pnl_percentage
                    FROM gold.indianstocks
                    -- where stock_code in ('VIRAT', 'RELIANCE')
                    GROUP BY 
                        "ISIN", stock_code, stock_name , business_date
                    ORDER BY 
                        business_date DESC
                """;
        return jdbcTemplate.query("SELECT * FROM (" + sql + ") latest "
                + "WHERE avg_pnl_percentage IS NOT NULL AND business_date = (SELECT MAX(business_date) FROM gold.indianstocks) "
                + "ORDER BY avg_pnl_percentage " + direction + " LIMIT ?",
                summaryMapper(), limit);
    }

    public LocalDate latestBusinessDate() {
        return jdbcTemplate.queryForObject("SELECT MAX(business_date) FROM gold.indianstocks", LocalDate.class);
    }

    public long trackedStocks() {
        Long count = jdbcTemplate.queryForObject("SELECT COUNT(DISTINCT stock_code) FROM gold.indianstocks", Long.class);
        return count == null ? 0 : count;
    }

    public java.math.BigDecimal averagePnlPercentage() {
        return jdbcTemplate.queryForObject("SELECT AVG(pnl_percentage) FROM gold.indianstocks", java.math.BigDecimal.class);
    }

    public boolean goldTableAvailable() {
        Boolean available = jdbcTemplate.queryForObject("""
                SELECT EXISTS (SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'gold' AND table_name = 'indianstocks')
                """, Boolean.class);
        return Boolean.TRUE.equals(available);
    }

    private org.springframework.jdbc.core.RowMapper<StockSummary> summaryMapper() {
        return (rs, rowNum) -> new StockSummary(
                rs.getString("stock_code"), rs.getString("stock_name"), rs.getString("isin"),
                rs.getObject("business_date", LocalDate.class), rs.getBigDecimal("closing_price"),
                rs.getBigDecimal("pnl_percentage"), rs.getBigDecimal("avg_pnl_percentage")
        );
    }
}