package com.stocksight.auth.auth;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Component;

@Component
@Profile("dev")
public class LoggingOtpSender implements OtpSender {
    private static final Logger logger = LoggerFactory.getLogger(LoggingOtpSender.class);

    @Override
    public void send(String email, String code) {
        logger.info("Development OTP generated for {}: {}", email, code);
    }
}
