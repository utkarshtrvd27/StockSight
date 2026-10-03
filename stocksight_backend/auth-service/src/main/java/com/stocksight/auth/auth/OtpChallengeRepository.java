package com.stocksight.auth.auth;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.UUID;

@Repository
public class OtpChallengeRepository {
    private final JdbcTemplate jdbcTemplate;

    public OtpChallengeRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public void create(UUID id, long userId, String otpHash, Instant expiresAt) {
        jdbcTemplate.update(
                "INSERT INTO otp_challenges (id, user_id, otp_hash, expires_at) VALUES (?, ?, ?, ?)",
                id, userId, otpHash, expiresAt);
    }

    public OtpChallenge findActive(UUID id) {
        return jdbcTemplate.queryForObject(
                "SELECT id, user_id, otp_hash, expires_at, consumed_at, attempts FROM otp_challenges WHERE id = ?",
                (resultSet, rowNumber) -> new OtpChallenge(
                        resultSet.getObject("id", UUID.class),
                        resultSet.getLong("user_id"),
                        resultSet.getString("otp_hash"),
                        resultSet.getTimestamp("expires_at").toInstant(),
                        resultSet.getTimestamp("consumed_at") == null
                                ? null : resultSet.getTimestamp("consumed_at").toInstant(),
                        resultSet.getInt("attempts")),
                id);
    }

    public void incrementAttempts(UUID id) {
        jdbcTemplate.update("UPDATE otp_challenges SET attempts = attempts + 1 WHERE id = ?", id);
    }

    public void consume(UUID id) {
        jdbcTemplate.update("UPDATE otp_challenges SET consumed_at = CURRENT_TIMESTAMP WHERE id = ?", id);
    }

    public record OtpChallenge(UUID id, long userId, String otpHash, Instant expiresAt,
                                Instant consumedAt, int attempts) {
    }
}
