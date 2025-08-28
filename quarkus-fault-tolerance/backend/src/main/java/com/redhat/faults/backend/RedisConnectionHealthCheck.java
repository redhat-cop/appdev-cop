package com.redhat.faults.backend;

import java.time.Duration;

import org.eclipse.microprofile.health.HealthCheck;
import org.eclipse.microprofile.health.HealthCheckResponse;
import org.eclipse.microprofile.health.Readiness;

import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@Readiness
@ApplicationScoped
public class RedisConnectionHealthCheck implements HealthCheck {

    @Inject
    IncrementService service;

    @Override
    public HealthCheckResponse call() {
    	service.keys().await().atMost(Duration.ofMillis(1000));
        return HealthCheckResponse.up("Redis connection is healthy!");
    }
}