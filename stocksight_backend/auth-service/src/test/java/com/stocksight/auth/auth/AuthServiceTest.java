package com.stocksight.auth.auth;

import com.stocksight.auth.user.User;
import com.stocksight.auth.user.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

import java.time.Duration;
import java.time.Instant;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class AuthServiceTest {
    @Mock
    private UserRepository userRepository;
    @Mock
    private OtpChallengeRepository otpChallengeRepository;
    @Mock
    private OtpSender otpSender;
    @Mock
    private JwtService jwtService;

    private AuthService authService;
    private final BCryptPasswordEncoder passwordEncoder = new BCryptPasswordEncoder();

    @BeforeEach
    void setUp() {
        authService = new AuthService(userRepository, otpChallengeRepository, otpSender,
                passwordEncoder, jwtService, Duration.ofMinutes(5), 5);
    }

    @Test
    void registerNormalizesEmailAndHashesPassword() {
        User user = user(1, "user@example.com");
        when(userRepository.findByEmail("user@example.com")).thenReturn(Optional.empty());
        when(userRepository.create(eq("user@example.com"), any(String.class), eq("Test User")))
                .thenReturn(user);

        User result = authService.register(" User@Example.com ", "password123", "Test User");

        assertThat(result).isEqualTo(user);
        verify(userRepository).create(eq("user@example.com"),
            org.mockito.ArgumentMatchers.argThat(hash -> passwordEncoder.matches("password123", hash)),
            eq("Test User"));
    }

    @Test
    void registerRejectsExistingEmail() {
        when(userRepository.findByEmail("user@example.com")).thenReturn(Optional.of(user(1, "user@example.com")));

        assertThatThrownBy(() -> authService.register("user@example.com", "password123", "Test User"))
                .isInstanceOf(AuthService.AuthException.class)
                .hasMessage("An account already exists for this email");
    }

    @Test
    void verifyOtpConsumesChallengeAndIssuesToken() {
        UUID challengeId = UUID.randomUUID();
        User user = user(1, "user@example.com");
        OtpChallengeRepository.OtpChallenge challenge = new OtpChallengeRepository.OtpChallenge(
                challengeId, 1, passwordEncoder.encode("123456"), Instant.now().plusSeconds(60), null, 0);
        when(otpChallengeRepository.findActive(challengeId)).thenReturn(challenge);
        when(userRepository.findById(1)).thenReturn(user);
        when(jwtService.issue(1, "user@example.com", "USER")).thenReturn("token");

        AuthService.TokenResponse result = authService.verifyOtp(challengeId, "123456");

        assertThat(result.accessToken()).isEqualTo("token");
        assertThat(result.tokenType()).isEqualTo("Bearer");
        verify(otpChallengeRepository).consume(challengeId);
        verify(userRepository).markEmailVerified(1);
    }

    private User user(long id, String email) {
        return new User(id, email, "hash", "Test User", "USER", false, true, Instant.now());
    }
}
