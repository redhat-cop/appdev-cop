package com.example;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.containsString;
import static org.hamcrest.Matchers.not;

import org.junit.jupiter.api.Test;

import io.quarkus.test.junit.QuarkusTest;

@QuarkusTest
class GreetingResourceTest {

    @Test
    void greetWorldReturnsHello() {
        given()
                .when().get("/greet/World")
                .then()
                .statusCode(200)
                .body(containsString("Hello, World!"));
    }

    @Test
    void countEndpointReturns200() {
        given()
                .when().get("/greet/count")
                .then()
                .statusCode(200)
                .body(containsString("\"count\""))
                .body(not(containsString("Hello, count")));
    }
}
