package com.example;

import io.smallrye.mutiny.Multi;
import io.smallrye.mutiny.Uni;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.NotFoundException;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import java.net.URI;

/**
 * REST endpoints backed by Hibernate Reactive Panache.
 * Return types use Mutiny so the stack stays non-blocking end-to-end where supported.
 */
@Path("/movies")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class MovieResource {

    /**
     * Streams all movies as a {@link Multi}; each item is emitted as it becomes available from the list.
     */
    @GET
    public Multi<Movie> listAll() {
        return Movie.<Movie>listAll()
                .onItem()
                .transformToMulti(movies -> Multi.createFrom().iterable(movies));
    }

    @GET
    @Path("/{id}")
    public Uni<Movie> get(@PathParam("id") Long id) {
        return Movie.<Movie>findById(id)
                .onItem()
                .ifNull()
                .switchTo(() -> Uni.createFrom().failure(new NotFoundException("Movie not found: " + id)));
    }

    @POST
    public Uni<Response> create(Movie movie) {
        return movie.persist()
                .replaceWith(Response.created(URI.create("/movies/" + movie.id)).entity(movie).build());
    }
}
