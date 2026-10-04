package com.stocksight.auth.auth;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSender;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.verify;

@ExtendWith(MockitoExtension.class)
class SmtpOtpSenderTest {
    @Mock
    private JavaMailSender mailSender;

    @Test
    void sendsOtpByEmailWithoutLoggingIt() {
        SmtpOtpSender otpSender = new SmtpOtpSender(mailSender, "smtp.example.com", "no-reply@example.com");

        otpSender.send("user@example.com", "123456");

        ArgumentCaptor<SimpleMailMessage> messageCaptor = ArgumentCaptor.forClass(SimpleMailMessage.class);
        verify(mailSender).send(messageCaptor.capture());
        SimpleMailMessage message = messageCaptor.getValue();
        assertThat(message.getFrom()).isEqualTo("no-reply@example.com");
        assertThat(message.getTo()).containsExactly("user@example.com");
        assertThat(message.getSubject()).isEqualTo("Your StockSight verification code");
        assertThat(message.getText()).contains("123456");
    }

    @Test
    void rejectsMissingSmtpConfiguration() {
        assertThatThrownBy(() -> new SmtpOtpSender(mailSender, "", ""))
                .isInstanceOf(IllegalStateException.class)
                .hasMessage("SMTP_HOST must be configured outside the dev profile");
    }
}
