package org.acme;

import jakarta.inject.Inject;
import picocli.CommandLine.Command;
import picocli.CommandLine.Parameters;

@Command(name = "trip", mixinStandardHelpOptions = true)
public class TripCommand implements Runnable {

    @Parameters(paramLabel = "<destination>", defaultValue = "Barcelona",
            description = "The destination you want to travel to.")
    String destination;

    @Inject
    TravelPlanner planner;

    @Override
    public void run() {
        System.out.println(planner.plan(destination));
    }
}
