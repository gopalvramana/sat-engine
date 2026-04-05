package com.satengine.dto;

import java.util.UUID;

/**
 * Request body for the Find My Gap AI diagnosis endpoint.
 * studentAnswer is the letter the student chose (e.g. "B").
 */
public record GapAnalysisRequest(UUID questionId, String studentAnswer) {}
