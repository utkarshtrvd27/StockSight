package com.stocksight.rest.stock;

import com.stocksight.rest.stock.StockModels.MarketOverview;
import com.stocksight.rest.stock.StockModels.PipelineStatus;
import com.stocksight.rest.stock.StockModels.StockPrice;
import com.stocksight.rest.stock.StockModels.StockSearchResult;
import com.stocksight.rest.stock.StockModels.StockSummary;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDate;
import java.util.List;

@RestController
@RequestMapping("/api/v1")
public class StockController {
    private final StockService service;

    public StockController(StockService service) {
        this.service = service;
    }

    @GetMapping("/market/overview")
    public MarketOverview overview() {
        return service.overview();
    }

    @GetMapping({"/stocks/search", "/stocks/search/"})
    public List<StockSearchResult> searchSuggestions(@RequestParam(required = false) String query,
                                                     @RequestParam(defaultValue = "10") int limit) {
        return service.searchSuggestions(query, limit);
    }

    @GetMapping("/stocks/{stockCode}")
    public StockSummary details(@PathVariable String stockCode) {
        return service.latest(stockCode);
    }

    @GetMapping("/stocks/history/{stockCode}")
    public List<StockPrice> history(@PathVariable String stockCode,
                                    @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate from,
                                    @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate to,
                                    @RequestParam(defaultValue = "14") int limit) {
        return service.history(stockCode, from, to, limit);
    }

    @GetMapping("/market/gainers")
    public List<StockSummary> gainers(@RequestParam(defaultValue = "20") int limit) {
        return service.movers(true, limit);
    }

    @GetMapping("/market/losers")
    public List<StockSummary> losers(@RequestParam(defaultValue = "20") int limit) {
        return service.movers(false, limit);
    }

    @GetMapping("/pipeline/status")
    public ResponseEntity<PipelineStatus> pipelineStatus() {
        PipelineStatus status = service.pipelineStatus();
        return ResponseEntity.status(status.databaseReachable() ? 200 : 503).body(status);
    }
}