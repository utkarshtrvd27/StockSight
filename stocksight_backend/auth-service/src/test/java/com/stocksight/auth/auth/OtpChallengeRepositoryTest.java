package com.stocksight.auth.auth;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.jdbc.core.JdbcTemplate;

import java.sql.Timestamp;
import java.time.Instant;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;

class OtpChallengeRepositoryTest {
    @Test
    void createBindsExpiryAsSqlTimestamp() {
        JdbcTemplate jdbcTemplate = mock(JdbcTemplate.class);
        OtpChallengeRepository repository = new OtpChallengeRepository(jdbcTemplate);
        UUID challengeId = UUID.randomUUID();
        long userId = 42L;
        String otpHash = "encoded-otp";
        Instant expiresAt = Instant.parse("2026-10-11T12:00:00Z");
        ArgumentCaptor<Object[]> arguments = ArgumentCaptor.forClass(Object[].class);

        repository.create(challengeId, userId, otpHash, expiresAt);

        verify(jdbcTemplate).update(
                eq("INSERT INTO auth.otp_challenges (id, user_id, otp_hash, expires_at) VALUES (?, ?, ?, ?)"),
                arguments.capture());
        assertThat(arguments.getValue()).containsExactly(
                challengeId, userId, otpHash, Timestamp.from(expiresAt));
    }
}
