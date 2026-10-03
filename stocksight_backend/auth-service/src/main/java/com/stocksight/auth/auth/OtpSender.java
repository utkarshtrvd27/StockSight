package com.stocksight.auth.auth;

public interface OtpSender {
    void send(String email, String code);
}
