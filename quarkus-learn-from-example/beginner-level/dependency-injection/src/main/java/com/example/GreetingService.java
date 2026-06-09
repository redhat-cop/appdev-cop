package com.example;

import jakarta.enterprise.context.ApplicationScoped;

/**
 * A CDI bean managed by Quarkus ArC.
 * <p>
 * {@link ApplicationScoped} means one shared instance for the whole application lifecycle.
 * The bean is created lazily on first use, then reused for all injections until the app stops.
 * This is the most common scope for stateless services like this one.
 */
@ApplicationScoped
public class GreetingService {

    public String greeting(String name) {
        return "Hello, " + name + "!";
    }

    public String farewell(String name) {
        return "Goodbye, " + name + "!";
    }
}
