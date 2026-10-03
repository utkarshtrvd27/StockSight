package com.stocksight.rest.error;

import com.stocksight.rest.stock.StockService.StockNotFoundException;
import org.springframework.jdbc.CannotGetJdbcConnectionException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.Map;

@RestControllerAdvice
public class ApiExceptionHandler {
    private static final Logger logger = LoggerFactory.getLogger(ApiExceptionHandler.class);

    @ExceptionHandler(StockNotFoundException.class)
    public org.springframework.http.ResponseEntity<Map<String, String>> notFound(StockNotFoundException exception) {
        return org.springframework.http.ResponseEntity.status(HttpStatus.NOT_FOUND)
                .body(Map.of("error", exception.getMessage()));
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public org.springframework.http.ResponseEntity<Map<String, String>> badRequest(IllegalArgumentException exception) {
        return org.springframework.http.ResponseEntity.badRequest()
                .body(Map.of("error", exception.getMessage()));
    }

    @ExceptionHandler(CannotGetJdbcConnectionException.class)
    public ResponseEntity<Map<String, String>> databaseConnectionFailed(
            CannotGetJdbcConnectionException exception) {
        logger.error("Database connection failed while processing request", exception);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "Connection failed with Database"));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, String>> internalServerError(Exception exception) {
        logger.error("Unhandled exception while processing request", exception);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "An unexpected error occurred"));
    }
}