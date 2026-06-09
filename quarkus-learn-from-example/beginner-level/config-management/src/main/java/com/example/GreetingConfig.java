package com.example;

import io.smallrye.config.ConfigMapping;

import java.util.Optional;

/**
 * Type-safe configuration grouped under the {@code greeting.*} prefix.
 * <p>
 * {@link ConfigMapping} is the preferred approach in Quarkus 3.x: one interface describes
 * several related keys, with methods mapping to property names (e.g. {@code defaultName()}
 * maps to {@code greeting.default-name} via standard naming convention).
 * </p>
 * <p>
 * {@link org.eclipse.microprofile.config.inject.ConfigProperty @ConfigProperty} injects a
 * single key at a time and is still valid; use it for one-off values or when a mapping
 * interface would be overkill.
 * </p>
 */
@ConfigMapping(prefix = "greeting")
public interface GreetingConfig {

    String message();

    String defaultName();

    Optional<String> suffix();
}
