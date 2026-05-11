package com.example;

import io.quarkus.hibernate.orm.panache.PanacheEntityBase;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.SequenceGenerator;
import jakarta.persistence.Table;

import java.util.List;

/**
 * Active Record: persistence helpers live on the entity type via {@link PanacheEntityBase} (list,
 * persist, delete, etc.), so you skip a separate repository for straightforward CRUD.
 *
 * <p>{@link io.quarkus.hibernate.orm.panache.PanacheEntity} is the same idea with a built-in
 * {@code id} field. Here the key and sequence name are declared explicitly so {@code import.sql}
 * can reference {@code Tasks_SEQ}, matching common Hibernate sequence naming for this table.
 */
@Entity
@Table(name = "tasks")
public class Task extends PanacheEntityBase {

    @Id
    @GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "tasksSeq")
    @SequenceGenerator(name = "tasksSeq", sequenceName = "Tasks_SEQ", allocationSize = 1)
    public Long id;

    @Column(nullable = false)
    public String title;

    @Column(nullable = false)
    public boolean completed;

    public static List<Task> findByCompleted(boolean completed) {
        return list("completed", completed);
    }
}
