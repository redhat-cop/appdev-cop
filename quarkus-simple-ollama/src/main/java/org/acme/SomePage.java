package org.acme;

import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.model.ollama.OllamaChatModel;
import io.quarkus.qute.Template;
import io.quarkus.qute.TemplateInstance;

import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.QueryParam;
import jakarta.ws.rs.core.MediaType;
import java.time.Duration;

import static java.util.Objects.requireNonNull;
import org.jboss.logmanager.StandardOutputStreams;

@Path("/start")
public class SomePage {

  private final Template page;

  public SomePage(Template page) {
    this.page = requireNonNull(page, "page is required");
  }

  @GET
  @Produces(MediaType.TEXT_HTML)
  public TemplateInstance get(@QueryParam("name") String name) {
    StandardOutputStreams.stdout.println("Hello World");

    ChatLanguageModel model = OllamaChatModel.builder().timeout(Duration.ofMinutes(5))
        .baseUrl("http://localhost:11434")
        .modelName("llama3.1")
        .build();

    String answer = model.generate("what is the air speed velocity of an unladen swallow");
    System.out.println(answer);
    answer = answer.replace("\r\n", "<br />").replace("\n", "<br />");

    return page.data("name", name, "answer", answer);
  }

}
