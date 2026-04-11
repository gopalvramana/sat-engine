package com.satengine.admin;

import ch.qos.logback.classic.spi.ILoggingEvent;
import ch.qos.logback.core.AppenderBase;

import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentLinkedDeque;

/**
 * Custom Logback appender that captures log lines per pipeline job.
 * <p>
 * When a job thread sets MDC key {@code "pipelineJobId"}, all log events
 * emitted from that thread (and its task) are written into the job's deque.
 * PipelineJobService registers a deque in JOB_LOGS before launching a job,
 * and reads from it to serve the polling endpoint.
 */
public class JobLogAppender extends AppenderBase<ILoggingEvent> {

    /**
     * Static map shared across all appender instances (Logback may create one per
     * context, but they all share this same map).
     * Key = jobId, Value = log lines deque (capped at 500 by PipelineJobService).
     */
    static final ConcurrentHashMap<String, ConcurrentLinkedDeque<String>> JOB_LOGS =
            new ConcurrentHashMap<>();

    @Override
    protected void append(ILoggingEvent event) {
        String jobId = event.getMDCPropertyMap().get("pipelineJobId");
        if (jobId == null) return;

        ConcurrentLinkedDeque<String> logs = JOB_LOGS.get(jobId);
        if (logs == null) return;

        logs.add(event.getFormattedMessage());
    }
}
