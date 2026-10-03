package com.stocksight.rest.stock;

import com.stocksight.rest.stock.StockModels.MarketOverview;
import com.stocksight.rest.stock.StockModels.PipelineStatus;
import com.stocksight.rest.stock.StockModels.StockSearchResult;
import com.stocksight.rest.stock.StockModels.StockSummary;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.jdbc.CannotGetJdbcConnectionException;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(StockController.class)
class StockControllerApiTest {
    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private StockService stockService;

        @Test
        void searchSuggestionsReturnsLightweightResults() throws Exception {
                when(stockService.searchSuggestions(eq("fos"), eq(10)))
                        .thenReturn(List.of(new StockSearchResult("INFY", "Infosys Ltd.", "INE009A01021")));

                mockMvc.perform(get("/api/v1/stocks/search")
                                .param("query", "fos")
                                .param("limit", "10"))
                        .andExpect(status().isOk())
                        .andExpect(content().contentTypeCompatibleWith("application/json"))
                        .andExpect(jsonPath("$[0].stockCode").value("INFY"))
                        .andExpect(jsonPath("$[0].stockName").value("Infosys Ltd."))
                        .andExpect(jsonPath("$[0].isin").value("INE009A01021"));
        }

        @Test
        void searchSuggestionsUsesDefaultLimit() throws Exception {
                when(stockService.searchSuggestions(eq("inf"), eq(10))).thenReturn(List.of());

                mockMvc.perform(get("/api/v1/stocks/search").param("query", "inf"))
                        .andExpect(status().isOk())
                        .andExpect(jsonPath("$").isArray())
                        .andExpect(jsonPath("$").isEmpty());
        }

        @Test
        void searchSuggestionsAcceptsTrailingSlash() throws Exception {
                when(stockService.searchSuggestions(eq("IN"), eq(10)))
                        .thenReturn(List.of(new StockSearchResult("INFY", "Infosys Ltd.", "INE009A01021")));

                mockMvc.perform(get("/api/v1/stocks/search/").param("query", "IN"))
                        .andExpect(status().isOk())
                        .andExpect(jsonPath("$[0].stockCode").value("INFY"));
        }

        @Test
        void latestStockReturnsSummaryDetails() throws Exception {
                StockSummary summary = summary();
                when(stockService.latest(eq("INFY"))).thenReturn(summary);

                mockMvc.perform(get("/api/v1/stocks/INFY"))
                        .andExpect(status().isOk())
                        .andExpect(jsonPath("$.stockCode").value("INFY"))
                        .andExpect(jsonPath("$.stockName").value("Infosys Ltd."))
                        .andExpect(jsonPath("$.closingPrice").value(1500.25))
                        .andExpect(jsonPath("$.pnlPercentage").value(0.35));
        }

        @Test
        void historyAcceptsDateRangeAndLimit() throws Exception {
                when(stockService.history(eq("INFY"), eq(LocalDate.of(2026, 9, 1)),
                        eq(LocalDate.of(2026, 9, 5)), eq(5))).thenReturn(List.of());

                mockMvc.perform(get("/api/v1/stocks/history/INFY")
                                .param("from", "2026-09-01")
                                .param("to", "2026-09-05")
                                .param("limit", "5"))
                        .andExpect(status().isOk())
                        .andExpect(jsonPath("$").isArray())
                        .andExpect(jsonPath("$").isEmpty());
        }

        @Test
        void invalidDateRangeReturnsBadRequest() throws Exception {
                when(stockService.history(eq("INFY"), eq(LocalDate.of(2026, 9, 5)),
                        eq(LocalDate.of(2026, 9, 1)), eq(14)))
                        .thenThrow(new IllegalArgumentException("from must be before or equal to to"));

                mockMvc.perform(get("/api/v1/stocks/history/INFY")
                                .param("from", "2026-09-05")
                                .param("to", "2026-09-01"))
                        .andExpect(status().isBadRequest())
                        .andExpect(jsonPath("$.error").value("from must be before or equal to to"));
        }

        @Test
        void overviewReturnsMarketSummary() throws Exception {
                MarketOverview overview = new MarketOverview(LocalDate.of(2026, 9, 5), 100,
                        new BigDecimal("0.42"), List.of(summary()), List.of(summary()));
                when(stockService.overview()).thenReturn(overview);

                mockMvc.perform(get("/api/v1/market/overview"))
                        .andExpect(status().isOk())
                        .andExpect(jsonPath("$.trackedStocks").value(100))
                        .andExpect(jsonPath("$.averagePnlPercentage").value(0.42));
        }

        @Test
        void gainersRouteReturnsResultsWithDefaultLimit() throws Exception {
                when(stockService.movers(true, 20)).thenReturn(List.of(summary()));

                mockMvc.perform(get("/api/v1/market/gainers"))
                                .andExpect(status().isOk())
                                .andExpect(jsonPath("$[0].stockCode").value("INFY"));
        }

        @Test
        void unexpectedGainersFailureReturnsSafeInternalServerError() throws Exception {
                when(stockService.movers(true, 20))
                        .thenThrow(new IllegalStateException("database details must not be exposed"));

                mockMvc.perform(get("/api/v1/market/gainers"))
                        .andExpect(status().isInternalServerError())
                        .andExpect(jsonPath("$.error").value("An unexpected error occurred"));
        }

        @Test
        void databaseConnectionFailureReturnsSpecificInternalServerError() throws Exception {
                when(stockService.movers(true, 20))
                        .thenThrow(new CannotGetJdbcConnectionException("connection refused"));

                mockMvc.perform(get("/api/v1/market/gainers"))
                        .andExpect(status().isInternalServerError())
                        .andExpect(jsonPath("$.error").value("Connection failed with Database"));
        }

        @Test
        void pipelineStatusReturnsServiceUnavailableWhenDatabaseIsDown() throws Exception {
                when(stockService.pipelineStatus()).thenReturn(new PipelineStatus(false, false, null));

                mockMvc.perform(get("/api/v1/pipeline/status"))
                        .andExpect(status().isServiceUnavailable())
                        .andExpect(jsonPath("$.databaseReachable").value(false))
                        .andExpect(jsonPath("$.goldTableAvailable").value(false));
        }

    private StockSummary summary() {
        return new StockSummary("INFY", "Infosys Ltd.", "INE009A01021",
                LocalDate.of(2026, 9, 5), new BigDecimal("1500.25"),
                new BigDecimal("0.35"), new BigDecimal("0.30"));
    }
}
