package com.example;

import io.quarkus.test.junit.QuarkusTest;
import io.restassured.http.ContentType;
import org.junit.jupiter.api.Test;

import static io.restassured.RestAssured.given;
import static org.hamcrest.CoreMatchers.is;
import static org.hamcrest.Matchers.greaterThanOrEqualTo;
import static org.hamcrest.Matchers.notNullValue;

@QuarkusTest
class MovieResourceTest {

    @Test
    void listIncludesSeedData() {
        given()
                .when().get("/movies")
                .then()
                .statusCode(200)
                .body("size()", greaterThanOrEqualTo(3));
    }

    @Test
    void createReturns201AndLocation() {
        given()
                .contentType(ContentType.JSON)
                .body("{\"title\":\"Dune\",\"director\":\"Denis Villeneuve\",\"year\":2021}")
                .when().post("/movies")
                .then()
                .statusCode(201)
                .header("Location", notNullValue())
                .body("title", is("Dune"))
                .body("director", is("Denis Villeneuve"))
                .body("year", is(2021));
    }
}
