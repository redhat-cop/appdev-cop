package com.example;

import io.quarkus.hibernate.reactive.panache.PanacheEntity;
import jakarta.persistence.Entity;

/**
 * Movie entity persisted through Hibernate Reactive Panache.
 * Operations return Mutiny {@code Uni} / {@code Multi} from the Panache layer.
 */
@Entity
public class Movie extends PanacheEntity {

    public String title;

    public String director;

    public int year;

    public Movie() {
    }

    public Movie(String title, String director, int year) {
        this.title = title;
        this.director = director;
        this.year = year;
    }
}
