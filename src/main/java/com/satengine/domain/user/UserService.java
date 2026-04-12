package com.satengine.domain.user;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class UserService {

    private final UserRepository userRepository;

    /**
     * Finds an existing user by email or creates a new one.
     * Updates name and picture on every login so they stay in sync with Google.
     */
    @Transactional
    public User findOrCreate(String email, String name, String picture) {
        return userRepository.findByEmail(email)
                .map(u -> {
                    // Refresh display name and avatar on every login
                    boolean changed = false;
                    if (name != null && !name.equals(u.getName()))       { u.setName(name);       changed = true; }
                    if (picture != null && !picture.equals(u.getPicture())) { u.setPicture(picture); changed = true; }
                    return changed ? userRepository.save(u) : u;
                })
                .orElseGet(() -> userRepository.save(
                        User.builder()
                                .email(email)
                                .name(name)
                                .picture(picture)
                                .build()
                ));
    }
}
