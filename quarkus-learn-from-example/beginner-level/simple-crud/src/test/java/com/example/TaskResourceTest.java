package com.example;

import io.quarkus.test.junit.QuarkusTest;
import io.restassured.http.ContentType;
import org.junit.jupiter.api.Test;

import static io.restassured.RestAssured.given;
import static org.hamcrest.CoreMatchers.is;
import static org.hamcrest.Matchers.greaterThanOrEqualTo;
import static org.hamcrest.Matchers.notNullValue;

@QuarkusTest
class TaskResourceTest {

    @Test
    void listIncludesSeedData() {
        given()
                .when().get("/tasks")
                .then()
                .statusCode(200)
                .body("size()", greaterThanOrEqualTo(3));
    }

    @Test
    void createReturns201AndLocation() {
        given()
                .contentType(ContentType.JSON)
                .body("{\"title\":\"From test\",\"completed\":false}")
                .when().post("/tasks")
                .then()
                .statusCode(201)
                .header("Location", notNullValue())
                .body("title", is("From test"))
                .body("completed", is(false));
    }
}
