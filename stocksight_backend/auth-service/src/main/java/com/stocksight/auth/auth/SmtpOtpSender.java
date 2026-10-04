package com.stocksight.auth.auth;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Profile;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.stereotype.Component;

@Component
@Profile("!dev")
public class SmtpOtpSender implements OtpSender {
    private final JavaMailSender mailSender;
    private final String fromAddress;

    public SmtpOtpSender(
            JavaMailSender mailSender,
            @Value("${SMTP_HOST:}") String smtpHost,
            @Value("${stocksight.auth.otp.from:}") String fromAddress) {
        if (smtpHost.isBlank()) {
            throw new IllegalStateException("SMTP_HOST must be configured outside the dev profile");
        }
        if (fromAddress.isBlank()) {
            throw new IllegalStateException("OTP_FROM must be configured outside the dev profile");
        }
        this.mailSender = mailSender;
        this.fromAddress = fromAddress;
    }

    @Override
    public void send(String email, String code) {
        SimpleMailMessage message = new SimpleMailMessage();
        message.setFrom(fromAddress);
        message.setTo(email);
        message.setSubject("Your StockSight verification code");
        message.setText("Your StockSight verification code is: " + code
                + "\n\nIf you did not request this code, you can ignore this email.");
        mailSender.send(message);
    }
}
