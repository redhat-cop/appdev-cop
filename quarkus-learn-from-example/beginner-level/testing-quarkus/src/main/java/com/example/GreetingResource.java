package com.example;

import jakarta.inject.Inject;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;

@Path("/hello")
public class GreetingResource {

    @Inject
    GreetingService greetingService;

    @GET
    @Produces(MediaType.TEXT_PLAIN)
    public String hello() {
        return "Hello from Quarkus!";
    }

    /**
     * Declared before {@code {name}} so {@code /hello/json/...} is not captured as a single path segment.
     */
    @GET
    @Path("json/{name}")
    @Produces(MediaType.APPLICATION_JSON)
    public GreetingJson helloJson(@PathParam("name") String name) {
        return new GreetingJson(name, greetingService.greeting(name));
    }

    @GET
    @Path("{name}")
    @Produces(MediaType.TEXT_PLAIN)
    public String helloName(@PathParam("name") String name) {
        return greetingService.greeting(name);
    }
}
