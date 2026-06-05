package com.example;

import jakarta.inject.Inject;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;

import io.vertx.core.json.JsonObject;

/**
 * Exposes {@code GET /greet/count} as its own resource so it is not captured by
 * {@code /greet/{name}} (which would treat {@code "count"} as a name).
 */
@Path("/greet/count")
public class GreetCountResource {

    @Inject
    CounterService counterService;

    @GET
    @Produces(MediaType.APPLICATION_JSON)
    public JsonObject count() {
        return new JsonObject().put("count", counterService.getCount());
    }
}
