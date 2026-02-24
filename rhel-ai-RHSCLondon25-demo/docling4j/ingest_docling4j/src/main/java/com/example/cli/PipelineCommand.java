package com.example.cli;

import picocli.CommandLine;

@CommandLine.Command(
        name = "pipeline",
        mixinStandardHelpOptions = true,
        subcommands = {IngestCommand.class, QueryCommand.class}
)
public class PipelineCommand implements Runnable {

    @Override
    public void run() {
        System.out.println("Use subcommands: ingest or query");
    }

    public static void main(String[] args) {
        int exitCode = new CommandLine(new PipelineCommand()).execute(args);
        System.exit(exitCode);
    }
}