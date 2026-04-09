package com.satengine.domain.session;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "sessions")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Session {

    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    @Column(columnDefinition = "uuid", updatable = false, nullable = false)
    private UUID id;

    @Column(name = "user_id", columnDefinition = "uuid")
    private UUID userId;

    @Column(name = "session_type", nullable = false, length = 10)
    private String sessionType;

    @Column(name = "section", length = 20)
    private String section;

    @Column(name = "status", length = 15)
    @Builder.Default
    private String status = "active";

    @Column(name = "started_at")
    private OffsetDateTime startedAt;

    @Column(name = "completed_at")
    private OffsetDateTime completedAt;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "score", columnDefinition = "jsonb")
    private String score;

    /**
     * Optional domain quotas for this session — e.g. {"algebra":3,"geometry_trigonometry":4}
     * When set, questions are drawn from each domain until the quota is exhausted.
     * Stored as JSONB; deserialized as a simple String that we parse in the service.
     */
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "domain_counts", columnDefinition = "jsonb")
    private String domainCounts;

    /**
     * Per-domain difficulty ranges — e.g. {"algebra":{"min":1,"max":5},"geometry_trigonometry":{"min":6,"max":7}}
     * When null for a domain, defaults to full range (1–7).
     */
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "domain_difficulties", columnDefinition = "jsonb")
    private String domainDifficulties;

    @PrePersist
    protected void onCreate() {
        if (startedAt == null) {
            startedAt = OffsetDateTime.now();
        }
    }
}
