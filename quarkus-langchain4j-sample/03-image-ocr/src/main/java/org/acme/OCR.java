package org.acme;

import jakarta.enterprise.context.ApplicationScoped;

import dev.langchain4j.data.image.Image;
import dev.langchain4j.service.UserMessage;
import io.quarkiverse.langchain4j.RegisterAiService;

@RegisterAiService
@ApplicationScoped
public interface OCR {

    @UserMessage("""
            You take an image in and output the text extracted from the image.
            Translate it in English.
            """)
    String process(Image image);
}
