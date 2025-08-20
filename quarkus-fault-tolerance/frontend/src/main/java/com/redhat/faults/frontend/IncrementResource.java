package com.redhat.faults.frontend;

import java.time.temporal.ChronoUnit;
import java.util.Arrays;
import java.util.List;

import org.eclipse.microprofile.faulttolerance.Fallback;
import org.eclipse.microprofile.faulttolerance.Timeout;
import org.eclipse.microprofile.rest.client.inject.RestClient;

import io.smallrye.mutiny.Uni;
import jakarta.ws.rs.DELETE;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.PUT;
import jakarta.ws.rs.Path;

@Path("/increments")
public class IncrementResource {

    @RestClient
    IncrementService service;

    @GET
    @Timeout(unit = ChronoUnit.MILLIS, value = 500)
    @Fallback(fallbackMethod = "keysFallback")
    public Uni<List<String>> keys() {
        return service.keys();
    }
    
    Uni<List<String>> keysFallback() {
    	return Uni.createFrom().item(Arrays.asList("dummy response"));
    }

    @POST
    public Increment create(Increment increment) {
        return service.create(increment);
    }

    @GET
    @Path("/{key}")
    public Increment get(String key) {
        return service.get(key);
    }

    @PUT
    @Path("/{key}")
    public void increment(String key, Integer value) {
        service.increment(key, value);
    }

    @DELETE
    @Path("/{key}")
    public Uni<Void> delete(String key) {
        return service.delete(key);
    }
}
