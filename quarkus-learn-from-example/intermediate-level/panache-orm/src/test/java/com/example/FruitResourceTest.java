package com.example;

import io.quarkus.test.junit.QuarkusTest;
import io.restassured.http.ContentType;
import org.junit.jupiter.api.Test;

import static io.restassured.RestAssured.given;
import static org.hamcrest.CoreMatchers.is;
import static org.hamcrest.Matchers.greaterThanOrEqualTo;
import static org.hamcrest.Matchers.notNullValue;

@QuarkusTest
class FruitResourceTest {

    @Test
    void listIncludesSeedData() {
        given()
                .when().get("/fruits")
                .then()
                .statusCode(200)
                .body("size()", greaterThanOrEqualTo(3));
    }

    @Test
    void createReturns201AndLocation() {
        given()
                .contentType(ContentType.JSON)
                .body("{\"name\":\"Pear\",\"season\":\"Late Summer\"}")
                .when().post("/fruits")
                .then()
                .statusCode(201)
                .header("Location", notNullValue())
                .body("name", is("Pear"))
                .body("season", is("Late Summer"));
    }
}
