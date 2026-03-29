package com.satengine.pipeline;

public enum QuestionStatus {
    GENERATED, REVIEWED, ENRICHED, APPROVED, REJECTED;

    public String lower() { return name().toLowerCase(); }
}
