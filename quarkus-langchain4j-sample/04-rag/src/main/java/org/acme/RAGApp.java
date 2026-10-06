package org.acme;

import io.quarkus.runtime.Quarkus;
import io.quarkus.runtime.annotations.QuarkusMain;
import jakarta.inject.Inject;
import io.quarkus.runtime.QuarkusApplication;

@QuarkusMain
public class RAGApp implements QuarkusApplication {

    @Inject
    DocumentationAssistant assistant;

    @Override
    public int run(String... args) {
        String question = args.length > 0 ? String.join(" ", args)
                : "How does Quarkus achieve fast startup times?";
        String answer = assistant.ask(question);
        System.out.println(answer);
        return 0;
    }

    public static void main(String[] args) {
        Quarkus.run(RAGApp.class, args);
    }
}
