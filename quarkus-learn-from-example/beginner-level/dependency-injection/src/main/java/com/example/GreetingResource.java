package com.example;

import jakarta.inject.Inject;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;

import io.vertx.core.json.JsonObject;

/**
 * JAX-RS resource that receives managed beans via CDI.
 * <p>
 * {@link Inject} asks ArC (Quarkus's CDI implementation) to supply a bean instance.
 * For {@code @ApplicationScoped} types, ArC creates one shared instance and injects it
 * wherever requested. Types and qualifiers are resolved at build time where possible,
 * which keeps startup fast and failures visible early.
 */
@Path("/greet")
public class GreetingResource {

    @Inject
    GreetingService greetingService;

    @Inject
    CounterService counterService;

    @GET
    @Path("/{name}")
    @Produces(MediaType.APPLICATION_JSON)
    public JsonObject greet(@PathParam("name") String name) {
        int requestNumber = counterService.increment();
        String message = greetingService.greeting(name);
        return new JsonObject().put("message", message).put("requestNumber", requestNumber);
    }

    @GET
    @Path("/farewell/{name}")
    @Produces(MediaType.APPLICATION_JSON)
    public JsonObject farewell(@PathParam("name") String name) {
        String message = greetingService.farewell(name);
        return new JsonObject().put("message", message);
    }
}
