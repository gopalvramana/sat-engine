package com.satengine.domain.session;

import jakarta.persistence.*;
import lombok.*;

import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "session_answers")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class SessionAnswer {

    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    @Column(columnDefinition = "uuid", updatable = false, nullable = false)
    private UUID id;

    @Column(name = "session_id", nullable = false, columnDefinition = "uuid")
    private UUID sessionId;

    @Column(name = "question_id", nullable = false, columnDefinition = "uuid")
    private UUID questionId;

    @Column(name = "student_answer", length = 10)
    private String studentAnswer;

    @Column(name = "is_correct")
    private Boolean isCorrect;

    @Column(name = "answered_at")
    private OffsetDateTime answeredAt;

    @Column(name = "time_spent_seconds")
    private Integer timeSpentSeconds;

    @PrePersist
    protected void onCreate() {
        if (answeredAt == null) {
            answeredAt = OffsetDateTime.now();
        }
    }
}
