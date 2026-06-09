package com.example;

import io.quarkus.test.junit.QuarkusTest;
import io.restassured.RestAssured;
import org.junit.jupiter.api.Test;

import static org.hamcrest.CoreMatchers.is;

@QuarkusTest
class GreetingResourceTest {

    @Test
    void helloEndpoint() {
        RestAssured.given()
                .when().get("/hello")
                .then()
                .statusCode(200)
                .body(is("Hello from Quarkus!"));
    }

    @Test
    void helloNameEndpoint() {
        RestAssured.given()
                .when().get("/hello/Quarkus")
                .then()
                .statusCode(200)
                .body(is("Hello, Quarkus!"));
    }
}
