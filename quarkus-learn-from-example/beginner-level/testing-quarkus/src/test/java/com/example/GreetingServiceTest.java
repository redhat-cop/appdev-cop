package com.example;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

/**
 * Plain unit tests run without starting Quarkus: no CDI container, no HTTP port, fastest feedback.
 * Use them for pure logic (formatting, calculations, mapping) on classes you can construct
 * directly or test with minimal collaborators.
 *
 * Prefer {@link io.quarkus.test.junit.QuarkusTest} when you need real injection, REST endpoints,
 * persistence, messaging, or other framework integrations under test.
 */
class GreetingServiceTest {

    @Test
    void greeting_returnsFormattedMessage() {
        GreetingService service = new GreetingService();
        assertEquals("Hello, World!", service.greeting("World"));
    }
}
