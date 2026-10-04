package com.stocksight.auth.user;

import org.springframework.dao.EmptyResultDataAccessException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public class UserRepository {
    private final JdbcTemplate jdbcTemplate;

    public UserRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public Optional<User> findByEmail(String email) {
        try {
            return Optional.ofNullable(jdbcTemplate.queryForObject(
                    "SELECT id, email, password_hash, display_name, role, email_verified, enabled, created_at "
                            + "FROM auth.users_table WHERE email = ?",
                    (resultSet, rowNumber) -> new User(
                            resultSet.getLong("id"),
                            resultSet.getString("email"),
                            resultSet.getString("password_hash"),
                            resultSet.getString("display_name"),
                            resultSet.getString("role"),
                            resultSet.getBoolean("email_verified"),
                            resultSet.getBoolean("enabled"),
                            resultSet.getTimestamp("created_at").toInstant()),
                    email));
        } catch (EmptyResultDataAccessException exception) {
            return Optional.empty();
        }
    }

        public User findById(long userId) {
        return jdbcTemplate.queryForObject(
            "SELECT id, email, password_hash, display_name, role, email_verified, enabled, created_at "
                + "FROM auth.users_table WHERE id = ?",
            (resultSet, rowNumber) -> new User(
                resultSet.getLong("id"),
                resultSet.getString("email"),
                resultSet.getString("password_hash"),
                resultSet.getString("display_name"),
                resultSet.getString("role"),
                resultSet.getBoolean("email_verified"),
                resultSet.getBoolean("enabled"),
                resultSet.getTimestamp("created_at").toInstant()),
            userId);
        }

    public User create(String email, String passwordHash, String displayName) {
        return jdbcTemplate.queryForObject(
                "INSERT INTO auth.users_table (email, password_hash, display_name) VALUES (?, ?, ?) "
                        + "RETURNING id, email, password_hash, display_name, role, email_verified, enabled, created_at",
                (resultSet, rowNumber) -> new User(
                        resultSet.getLong("id"),
                        resultSet.getString("email"),
                        resultSet.getString("password_hash"),
                        resultSet.getString("display_name"),
                        resultSet.getString("role"),
                        resultSet.getBoolean("email_verified"),
                        resultSet.getBoolean("enabled"),
                        resultSet.getTimestamp("created_at").toInstant()),
                email, passwordHash, displayName);
    }

    public void markEmailVerified(long userId) {
        jdbcTemplate.update("UPDATE auth.users_table SET email_verified = TRUE WHERE id = ?", userId);
    }
}
