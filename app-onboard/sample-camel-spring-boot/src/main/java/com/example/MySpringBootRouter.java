package com.example;

import org.apache.camel.builder.RouteBuilder;
import org.apache.camel.model.rest.RestBindingMode;
import org.springframework.stereotype.Component;
import org.springframework.http.MediaType;

/**
 * A simple Camel route that triggers from a timer and calls a bean and prints
 * to system out.
 *
 * Use @Component to make Camel auto detect this route when starting.
 */
@Component
public class MySpringBootRouter extends RouteBuilder {

  @Override
  public void configure() {

    restConfiguration()
        .component("servlet")
        .bindingMode(RestBindingMode.auto)
        .dataFormatProperty("prettyPrint", "true")
        .apiContextPath("/api-doc")
        .apiProperty("api.title", "Sample Hello World Route")
        .apiProperty("api.version", "1.0.0");

    rest().path("/").description("main route")
        .get().produces(MediaType.TEXT_PLAIN_VALUE).routeId("rootPath")
        .to("direct:rootPath");
    from("direct:rootPath")
        .setBody(simple("Hello World from ${hostname} - ${date:now:dd-MMM-yy HH:mm}"));

    from("timer:hello?period={{timer.period}}").routeId("hello")
        .transform().method("myBean", "saySomething")
        .filter(simple("${body} contains 'foo'"))
        .to("log:foo")
        .end()
        .to("stream:out");
  }

}
