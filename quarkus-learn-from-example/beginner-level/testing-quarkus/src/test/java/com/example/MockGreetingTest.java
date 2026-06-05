package com.example;

import io.quarkus.test.junit.QuarkusTest;
import io.quarkus.test.junit.mockito.InjectMock;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;

import static io.restassured.RestAssured.given;
import static org.hamcrest.CoreMatchers.is;
import static org.mockito.ArgumentMatchers.anyString;

/**
 * {@link InjectMock} replaces the real CDI bean with a Mockito mock in the application under test.
 * Use it to isolate the layer you are testing (for example, force a service to throw or return
 * fixed data) without standing up databases or external systems.
 *
 * Do not over-mock: if the goal is to verify real integration between components,
 * use real beans and {@link QuarkusTest} without mocks instead.
 */
@QuarkusTest
class MockGreetingTest {

    @InjectMock
    GreetingService greetingService;

    @Test
    void helloName_usesMockedService() {
        Mockito.when(greetingService.greeting(anyString())).thenReturn("Howdy from the mock!");

        given()
                .when().get("/hello/Anyone")
                .then()
                .statusCode(200)
                .body(is("Howdy from the mock!"));

        Mockito.verify(greetingService).greeting("Anyone");
    }
}
