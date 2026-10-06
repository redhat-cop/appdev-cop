package org.acme;

import jakarta.inject.Inject;
import picocli.CommandLine;
import picocli.CommandLine.Command;
import picocli.CommandLine.Parameters;

@Command(name = "poem", mixinStandardHelpOptions = true)
public class PoemCommand implements Runnable {

    @Parameters(paramLabel = "<topic>", defaultValue = "quarkus",
            description = "The topic.")
    String topic;

    @CommandLine.Option(names = "--lines", defaultValue = "4",
            description = "The number of lines in the poem.")
    int lines;

    @Inject
    MyAiService myAiService;

    @Override
    public void run() {
        System.out.println(myAiService.writeAPoem(topic, lines));
    }
}
