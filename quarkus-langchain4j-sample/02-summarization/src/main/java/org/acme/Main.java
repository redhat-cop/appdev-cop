package org.acme;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;

import jakarta.inject.Inject;

import io.quarkus.runtime.Quarkus;
import io.quarkus.runtime.QuarkusApplication;
import io.quarkus.runtime.annotations.QuarkusMain;

@QuarkusMain
public class Main implements QuarkusApplication {

    @Inject
    SummarizationService ai;

    @Override
    public int run(String... args) throws IOException {
        if (args.length == 0) {
            System.err.println("Please provide the path to the text file as an argument.");
            return 1;
        }
        var article = Files.readString(new File(args[0]).toPath());
        System.out.println(ai.summarize(article));
        return 0;
    }

    public static void main(String[] args) {
        Quarkus.run(Main.class, args);
    }
}
