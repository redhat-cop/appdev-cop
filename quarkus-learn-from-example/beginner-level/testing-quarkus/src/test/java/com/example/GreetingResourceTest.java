package com.example;

import io.quarkus.test.junit.QuarkusTest;
import org.junit.jupiter.api.Test;

import static io.restassured.RestAssured.given;
import static org.hamcrest.CoreMatchers.equalTo;
import static org.hamcrest.CoreMatchers.is;

/**
 * <p>{@link QuarkusTest} starts a full application (CDI, HTTP stack, config) for the test class.
 * REST Assured is configured automatically with the correct test URL and port.</p>
 *
 * <p><strong>Lifecycle (typical):</strong> Quarkus boots the application once per test class
 * (shared JVM), runs {@code @BeforeAll} hooks from extensions, executes tests, then tears down.
 * Exact reuse rules depend on Quarkus version and annotations such as {@code @QuarkusIntegrationTest};
 * see the official "Testing" guide for transactional tests and {@code @TestProfile}.</p>
 */
@QuarkusTest
class GreetingResourceTest {

    @Test
    void testHelloEndpoint() {
        // given: optional request setup (headers, auth, body). Empty here.
        given()
                // when: send GET /hello
                .when().get("/hello")
                // then: assert HTTP status and plain-text body
                .then()
                .statusCode(200)
                .body(is("Hello from Quarkus!"));
    }

    @Test
    void testHelloName() {
        // given -> when -> then pattern for a path parameter
        given()
                .when().get("/hello/Quarkus")
                .then()
                .statusCode(200)
                .body(is("Hello, Quarkus!"));
    }

    @Test
    void testHelloJson() {
        // Hamcrest matchers on JSON fields (REST Assured JsonPath)
        given()
                .when().get("/hello/json/Quarkus")
                .then()
                .statusCode(200)
                .body("name", equalTo("Quarkus"))
                .body("message", equalTo("Hello, Quarkus!"));
    }

    @Test
    void testNotFoundEndpoint() {
        // Unknown path should return 404
        given()
                .when().get("/this/path/does/not/exist")
                .then()
                .statusCode(404);
    }
}
