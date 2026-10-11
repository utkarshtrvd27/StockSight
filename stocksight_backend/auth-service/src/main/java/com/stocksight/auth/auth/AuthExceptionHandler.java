package com.stocksight.auth.auth;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.Map;

@RestControllerAdvice
public class AuthExceptionHandler {
    @ExceptionHandler(AuthService.AuthException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public Map<String, String> handleAuthException(AuthService.AuthException exception) {
        return Map.of("error", exception.getMessage());
    }

    @ExceptionHandler(AuthService.InvalidCredentialsException.class)
    @ResponseStatus(HttpStatus.UNAUTHORIZED)
    public Map<String, String> handleInvalidCredentials(AuthService.InvalidCredentialsException exception) {
        return Map.of("error", exception.getMessage());
    }

    @ExceptionHandler(AuthService.EmailNotVerifiedException.class)
    @ResponseStatus(HttpStatus.FORBIDDEN)
    public Map<String, String> handleEmailNotVerified(AuthService.EmailNotVerifiedException exception) {
        return Map.of("error", exception.getMessage());
    }
}
