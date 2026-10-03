package com.stocksight.auth.user;

import java.time.Instant;

public record User(
        long id,
        String email,
        String passwordHash,
        String displayName,
        String role,
        boolean emailVerified,
        boolean enabled,
        Instant createdAt) {
}
