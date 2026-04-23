package com.satengine.domain.sympy;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface SymPyQuestionAnswerRepository extends JpaRepository<SymPyQuestionAnswer, UUID> {

    Optional<SymPyQuestionAnswer> findByQuestionId(UUID questionId);
}
