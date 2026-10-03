package com.stocksight.rest.stock;

import com.stocksight.rest.stock.StockModels.StockSearchResult;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.dao.DataAccessException;
import org.springframework.stereotype.Component;

import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.atomic.AtomicReference;

@Component
public class StockSearchCatalog {
    private static final Logger logger = LoggerFactory.getLogger(StockSearchCatalog.class);

    private final StockRepository repository;
    private final AtomicReference<List<StockSearchResult>> entries = new AtomicReference<>(List.of());

    public StockSearchCatalog(StockRepository repository) {
        this.repository = repository;
    }

    @EventListener(ApplicationReadyEvent.class)
    public void loadOnStartup() {
        refresh();
    }

    public void refresh() {
        try {
            entries.set(List.copyOf(repository.stockCatalog()));
            logger.info("Loaded {} stocks into the search catalog", entries.get().size());
        } catch (DataAccessException exception) {
            logger.warn("Could not load the stock search catalog; retaining the previous catalog", exception);
        }
    }

    public List<StockSearchResult> search(String query, int limit) {
        String normalizedQuery = normalize(query);
        if (normalizedQuery.isBlank() || limit <= 0) {
            return List.of();
        }

        return entries.get().stream()
                .filter(entry -> contains(entry, normalizedQuery))
            .sorted(Comparator.<StockSearchResult>comparingInt(entry -> matchRank(entry, normalizedQuery))
                        .thenComparing(entry -> normalize(entry.stockName()))
                        .thenComparing(entry -> normalize(entry.stockCode())))
                .limit(limit)
                .toList();
    }

    private boolean contains(StockSearchResult entry, String query) {
        return normalize(entry.stockCode()).contains(query)
                || normalize(entry.stockName()).contains(query);
    }

    private int matchRank(StockSearchResult entry, String query) {
        String code = normalize(entry.stockCode());
        String name = normalize(entry.stockName());
        if (code.equals(query)) {
            return 0;
        }
        if (code.startsWith(query)) {
            return 1;
        }
        if (name.startsWith(query)) {
            return 2;
        }
        return 3;
    }

    private String normalize(String value) {
        return value == null ? "" : value.trim().toUpperCase(Locale.ROOT);
    }
}