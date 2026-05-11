package com.example;

import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;

/**
 * JAX-RS resource: maps HTTP requests to Java methods.
 * Base path for all endpoints in this class.
 */
@Path("/hello")
public class GreetingResource {

    /**
     * {@code @GET} handles HTTP GET. Combined with class {@code @Path("/hello")},
     * this is served at {@code /hello}.
     */
    @GET
    @Produces(MediaType.TEXT_PLAIN)
    public String hello() {
        return "Hello from Quarkus!";
    }

    /**
     * {@code @Path("/{name}")} adds a path segment; {@code {name}} is a template
     * parameter injected into the method argument below.
     */
    @GET
    @Path("/{name}")
    @Produces(MediaType.TEXT_PLAIN)
    public String helloName(@PathParam("name") String name) {
        return "Hello, " + name + "!";
    }
}
