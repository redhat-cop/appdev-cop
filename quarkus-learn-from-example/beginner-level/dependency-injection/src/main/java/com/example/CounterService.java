package com.example;

import java.util.concurrent.atomic.AtomicInteger;

import jakarta.enterprise.context.ApplicationScoped;

/**
 * Demonstrates injecting multiple beans into a resource.
 * <p>
 * {@link AtomicInteger} uses compare-and-set operations internally so increment and read
 * stay consistent when many HTTP worker threads call this bean at once. A plain {@code int}
 * field would risk lost updates without synchronization.
 */
@ApplicationScoped
public class CounterService {

    private final AtomicInteger counter = new AtomicInteger(0);

    public int increment() {
        return counter.incrementAndGet(); // updates that require the new value for callers
    }

    public int getCount() {
        return counter.get(); // reads the latest visible value to other threads
    }
}
