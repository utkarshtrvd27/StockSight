package com.stocksight.auth.auth;

import com.stocksight.auth.user.User;
import com.stocksight.auth.user.UserRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.security.SecureRandom;
import java.time.Duration;
import java.time.Instant;
import java.util.Locale;
import java.util.UUID;

@Service
public class AuthService {
    private final UserRepository userRepository;
    private final OtpChallengeRepository otpChallengeRepository;
    private final OtpSender otpSender;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;
    private final Duration otpTtl;
    private final int maxOtpAttempts;
    private final SecureRandom secureRandom = new SecureRandom();

    public AuthService(UserRepository userRepository,
                       OtpChallengeRepository otpChallengeRepository,
                       OtpSender otpSender,
                       PasswordEncoder passwordEncoder,
                       JwtService jwtService,
                       @Value("${stocksight.auth.otp-ttl:PT5M}") Duration otpTtl,
                       @Value("${stocksight.auth.otp-max-attempts:5}") int maxOtpAttempts) {
        this.userRepository = userRepository;
        this.otpChallengeRepository = otpChallengeRepository;
        this.otpSender = otpSender;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
        this.otpTtl = otpTtl;
        this.maxOtpAttempts = maxOtpAttempts;
    }

    public User register(String email, String password, String displayName) {
        String normalizedEmail = normalizeEmail(email);
        if (userRepository.findByEmail(normalizedEmail).isPresent()) {
            throw new AuthException("An account already exists for this email");
        }
        try {
            return userRepository.create(normalizedEmail, passwordEncoder.encode(password), displayName.trim());
        } catch (DuplicateKeyException exception) {
            throw new AuthException("An account already exists for this email");
        }
    }

    public OtpChallengeResponse requestOtp(String email) {
        User user = userRepository.findByEmail(normalizeEmail(email))
                .orElseThrow(() -> new AuthException("No account exists for this email"));
        if (!user.enabled()) {
            throw new AuthException("This account is disabled");
        }

        String code = String.format("%06d", secureRandom.nextInt(1_000_000));
        UUID challengeId = UUID.randomUUID();
        otpChallengeRepository.create(challengeId, user.id(), passwordEncoder.encode(code),
                Instant.now().plus(otpTtl));
        otpSender.send(user.email(), code);
        return new OtpChallengeResponse(challengeId, otpTtl.toSeconds());
    }

    public TokenResponse verifyOtp(UUID challengeId, String code) {
        OtpChallengeRepository.OtpChallenge challenge = otpChallengeRepository.findActive(challengeId);
        if (challenge.consumedAt() != null || challenge.expiresAt().isBefore(Instant.now())) {
            throw new AuthException("OTP challenge is expired or already used");
        }
        if (challenge.attempts() >= maxOtpAttempts) {
            throw new AuthException("OTP attempt limit exceeded");
        }
        if (!passwordEncoder.matches(code, challenge.otpHash())) {
            otpChallengeRepository.incrementAttempts(challengeId);
            throw new AuthException("Invalid OTP");
        }

        otpChallengeRepository.consume(challengeId);
        User user = userRepository.findById(challenge.userId());
        userRepository.markEmailVerified(user.id());
        return new TokenResponse(jwtService.issue(user.id(), user.email(), user.role()), "Bearer");
    }

    public User findByEmail(String email) {
        return userRepository.findByEmail(normalizeEmail(email))
                .orElseThrow(() -> new AuthException("User not found"));
    }

    private String normalizeEmail(String email) {
        return email.trim().toLowerCase(Locale.ROOT);
    }

    public record OtpChallengeResponse(UUID challengeId, long expiresInSeconds) {
    }

    public record TokenResponse(String accessToken, String tokenType) {
    }

    public static class AuthException extends RuntimeException {
        public AuthException(String message) {
            super(message);
        }
    }
}
