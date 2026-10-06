package com.example;

import io.quarkus.hibernate.orm.panache.PanacheEntity;
import jakarta.persistence.Entity;

/**
 * Panache Active Record entity: persistence helpers live on the type itself
 * ({@code Fruit.listAll()}, {@code fruit.persist()}, and so on).
 */
@Entity
public class Fruit extends PanacheEntity {

    public String name;

    public String season;

    public Fruit() {
    }

    public Fruit(String name, String season) {
        this.name = name;
        this.season = season;
    }
}
