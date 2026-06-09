package com.example;

import jakarta.transaction.Transactional;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.DELETE;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.NotFoundException;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.PUT;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

import java.net.URI;
import java.util.List;

/**
 * JAX-RS resource exposing CRUD over {@link Task}. JSON is used for requests and responses.
 * <p>
 * Write operations are annotated with {@link Transactional} so each request runs in a transaction:
 * Hibernate can flush changes and the transaction commits when the method returns successfully.
 */
@Path("/tasks")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class TaskResource {

    /** List every task row (seed data comes from {@code import.sql} on startup). */
    @GET
    public List<Task> list() {
        return Task.listAll();
    }

    /** Return a single task by id, or HTTP 404 if it does not exist. */
    @GET
    @Path("/{id}")
    public Task get(@PathParam("id") Long id) {
        return Task.findByIdOptional(id).orElseThrow(NotFoundException::new);
    }

    /**
     * Create a new task. Responds with HTTP 201 and a {@code Location} header pointing at the new
     * resource so clients can follow up with {@code GET}.
     */
    @POST
    @Transactional
    public Response create(Task task) {
        task.persist();
        return Response.created(URI.create("/tasks/" + task.id)).entity(task).build();
    }

    /** Replace fields on an existing task; returns 404 if the id is unknown. */
    @PUT
    @Path("/{id}")
    @Transactional
    public Task update(@PathParam("id") Long id, Task incoming) {
        Task existing = Task.findByIdOptional(id).orElseThrow(NotFoundException::new);
        existing.title = incoming.title;
        existing.completed = incoming.completed;
        return existing;
    }

    /** Delete a task by id; HTTP 204 indicates success with no response body. */
    @DELETE
    @Path("/{id}")
    @Transactional
    public Response delete(@PathParam("id") Long id) {
        boolean deleted = Task.deleteById(id);
        if (!deleted) {
            throw new NotFoundException();
        }
        return Response.noContent().build();
    }
}
