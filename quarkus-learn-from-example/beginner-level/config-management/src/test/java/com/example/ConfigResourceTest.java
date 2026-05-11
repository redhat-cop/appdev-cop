package com.example;

import io.quarkus.test.junit.QuarkusTest;
import org.junit.jupiter.api.Test;

import static io.restassured.RestAssured.given;
import static org.hamcrest.CoreMatchers.containsString;

@QuarkusTest
class ConfigResourceTest {

    @Test
    void configReturns200() {
        given()
                .when().get("/config")
                .then()
                .statusCode(200);
    }

    @Test
    void greetUsesTestProfileMessage() {
        given()
                .when().get("/config/greet")
                .then()
                .statusCode(200)
                .body(containsString("Welcome to Quarkus (Test)"));
    }
}
