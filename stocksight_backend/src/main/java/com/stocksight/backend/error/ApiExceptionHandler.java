package com.stocksight.backend.error;

import com.stocksight.backend.stock.StockService.StockNotFoundException;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.Map;

@RestControllerAdvice
public class ApiExceptionHandler {
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
}