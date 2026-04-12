package com.satengine.domain.session;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.UUID;

public interface SessionRepository extends JpaRepository<Session, UUID> {

    List<Session> findByUserIdOrderByStartedAtDesc(UUID userId);

    @Query("""
        SELECT COUNT(s) FROM Session s
        WHERE s.userId = :userId AND s.status = 'completed'
        """)
    long countCompletedByUser(@Param("userId") UUID userId);
}
