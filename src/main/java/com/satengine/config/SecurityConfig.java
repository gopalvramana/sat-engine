package com.satengine.config;

import com.satengine.config.OAuth2SuccessHandler;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.oauth2.client.registration.ClientRegistrationRepository;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
@EnableWebSecurity
@RequiredArgsConstructor
public class SecurityConfig {

    private final OAuth2SuccessHandler oauth2SuccessHandler;

    @Bean
    public SecurityFilterChain filterChain(
            HttpSecurity http,
            @Autowired(required = false) ClientRegistrationRepository clientRegistrationRepository
    ) throws Exception {

        http
            // Disable CSRF for REST APIs — we use session cookies (same-origin only)
            .csrf(AbstractHttpConfigurer::disable)

            // All paths open for now; ownership enforcement comes in Phase 2 (#5)
            .authorizeHttpRequests(auth -> auth.anyRequest().permitAll())

            // Custom logout: clear session, redirect to /login
            .logout(logout -> logout
                    .logoutUrl("/api/auth/logout")
                    .invalidateHttpSession(true)
                    .deleteCookies("JSESSIONID")
                    .logoutSuccessUrl("/login")
            );

        // Only wire up OAuth2 login if Google credentials are present (not on local dev)
        if (clientRegistrationRepository != null) {
            http.oauth2Login(oauth2 -> oauth2
                    .loginPage("/login")
                    .successHandler(oauth2SuccessHandler)
            );
        }

        return http.build();
    }
}
