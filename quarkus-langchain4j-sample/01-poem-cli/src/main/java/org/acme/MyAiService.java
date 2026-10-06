package org.acme;

import jakarta.enterprise.context.ApplicationScoped;

import dev.langchain4j.service.SystemMessage;
import dev.langchain4j.service.UserMessage;
import io.quarkiverse.langchain4j.RegisterAiService;

@RegisterAiService
@SystemMessage("You are a professional poet")
@ApplicationScoped
public interface MyAiService {

    @UserMessage("""
                Write a poem about {topic}.
                The poem should be {lines} lines long.
            """)
    String writeAPoem(String topic, int lines);
}
