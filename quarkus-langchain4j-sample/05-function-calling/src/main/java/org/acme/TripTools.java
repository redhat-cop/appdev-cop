package org.acme;

import dev.langchain4j.agent.tool.Tool;
import jakarta.enterprise.context.ApplicationScoped;

@ApplicationScoped
public class TripTools {

    @Tool
    public String weather(String location) {
        // Simulate a weather API call
        return switch (location.toLowerCase()) {
            case "paris" -> "Rainy";
            case "barcelona" -> "Sunny";
            default -> "Unknown";
        };
    }

    @Tool
    public String activity(String weather) {
        return switch (weather.toLowerCase()) {
            case "rainy" -> "Visit a museum";
            case "sunny" -> "Go to the beach";
            default -> "Stay indoors with a good book";
        };
    }
}
