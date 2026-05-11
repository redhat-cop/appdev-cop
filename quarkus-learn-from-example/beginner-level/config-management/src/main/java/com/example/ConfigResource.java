package com.example;

import jakarta.inject.Inject;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import org.eclipse.microprofile.config.inject.ConfigProperty;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Demonstrates two configuration styles side by side:
 * <ul>
 *   <li>{@link GreetingConfig} — {@code @ConfigMapping} for a cohesive set of {@code greeting.*} keys.</li>
 *   <li>{@link org.eclipse.microprofile.config.inject.ConfigProperty} — injects {@code app.version} directly (older, per-property style).</li>
 * </ul>
 */
@Path("/config")
public class ConfigResource {

    @Inject
    GreetingConfig greetingConfig;

    @Inject
    @ConfigProperty(name = "app.version")
    String appVersion;

    @GET
    @Produces(MediaType.APPLICATION_JSON)
    public Map<String, Object> config() {
        Map<String, Object> greeting = new LinkedHashMap<>();
        greeting.put("message", greetingConfig.message());
        greeting.put("defaultName", greetingConfig.defaultName());
        greetingConfig.suffix().ifPresent(s -> greeting.put("suffix", s));

        Map<String, Object> body = new LinkedHashMap<>();
        body.put("appVersion", appVersion);
        body.put("greeting", greeting);
        return body;
    }

    @GET
    @Path("/greet")
    @Produces(MediaType.TEXT_PLAIN)
    public String greetDefault() {
        return formatGreeting(greetingConfig.defaultName());
    }

    @GET
    @Path("/greet/{name}")
    @Produces(MediaType.TEXT_PLAIN)
    public String greet(@PathParam("name") String name) {
        return formatGreeting(name);
    }

    private String formatGreeting(String name) {
        String suffix = greetingConfig.suffix().orElse("");
        return greetingConfig.message() + ", " + name + suffix;
    }
}
