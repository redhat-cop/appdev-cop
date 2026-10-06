package org.acme;

import dev.langchain4j.service.UserMessage;
import dev.langchain4j.service.SystemMessage;
import io.quarkiverse.langchain4j.RegisterAiService;
import io.quarkiverse.langchain4j.ToolBox;
import jakarta.enterprise.context.ApplicationScoped;

@RegisterAiService
@ApplicationScoped
@SystemMessage("""
    You are a smart travel planner. Your job is to help users plan their trips.
    You may call available tools to determine the weather and propose activities.
    Always reflect on tool results before giving a final answer.
""")
public interface TravelPlanner {

    @UserMessage("I want to go to {destination}. What should I do?")
    @ToolBox(TripTools.class)
    String plan(String destination);
}
