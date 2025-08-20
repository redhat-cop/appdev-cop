package com.redhat.faults.frontend;

import java.util.List;

import org.eclipse.microprofile.rest.client.inject.RegisterRestClient;

import io.smallrye.mutiny.Uni;
import jakarta.ws.rs.DELETE;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.PUT;
import jakarta.ws.rs.Path;

@Path("/increments")
@RegisterRestClient(configKey = "backend")
public interface IncrementService {

    @GET
    public Uni<List<String>> keys();

    @POST
    public Increment create(Increment increment);

    @GET
    @Path("/{key}")
    public Increment get(String key);

    @PUT
    @Path("/{key}")
    public void increment(String key, Integer value);

    @DELETE
    @Path("/{key}")
    public Uni<Void> delete(String key);
}

