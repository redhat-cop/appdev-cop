package com.example;

import io.quarkus.test.junit.QuarkusTest;
import io.restassured.http.ContentType;
import org.junit.jupiter.api.Test;

import static io.restassured.RestAssured.given;
import static org.hamcrest.CoreMatchers.is;

@QuarkusTest
class QuoteResourceTest {

    @Test
    void publishQuoteReturnsAccepted() {
        given()
                .contentType(ContentType.JSON)
                .body("{\"author\":\"Kafka\",\"text\":\"Publish early, publish often.\"}")
                .when().post("/quotes")
                .then()
                .statusCode(202)
                .body("author", is("Kafka"))
                .body("text", is("Publish early, publish often."));
    }
}
