package com.stocksight.auth.auth;

import com.stocksight.auth.user.User;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.UUID;

@RestController
@RequestMapping("/api/v1/auth")
public class AuthController {
    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    @PostMapping("/register")
    public UserResponse register(@Valid @RequestBody RegisterRequest request) {
        return UserResponse.from(authService.register(request.email(), request.password(), request.displayName()));
    }

    @PostMapping("/otp/request")
    public AuthService.OtpChallengeResponse requestOtp(@Valid @RequestBody EmailRequest request) {
        return authService.requestOtp(request.email());
    }

    @PostMapping("/otp/verify")
    public AuthService.TokenResponse verifyOtp(@Valid @RequestBody VerifyOtpRequest request) {
        return authService.verifyOtp(request.challengeId(), request.code());
    }

    @GetMapping("/me")
    public UserResponse me(@AuthenticationPrincipal String email) {
        return UserResponse.from(authService.findByEmail(email));
    }

    public record RegisterRequest(
            @NotBlank @Email String email,
            @NotBlank @Size(min = 8, max = 128) String password,
            @NotBlank @Size(max = 120) String displayName) {
    }

    public record EmailRequest(@NotBlank @Email String email) {
    }

    public record VerifyOtpRequest(@NotNull UUID challengeId,
                                   @NotBlank @Size(min = 6, max = 6) String code) {
    }

    public record UserResponse(long id, String email, String displayName, String role,
                               boolean emailVerified, boolean enabled) {
        static UserResponse from(User user) {
            return new UserResponse(user.id(), user.email(), user.displayName(), user.role(),
                    user.emailVerified(), user.enabled());
        }
    }
}
