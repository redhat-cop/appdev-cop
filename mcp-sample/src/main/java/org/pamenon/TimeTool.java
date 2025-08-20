package org.pamenon;

import io.quarkiverse.mcp.server.Tool;
import io.quarkiverse.mcp.server.ToolArg;
import jakarta.enterprise.context.ApplicationScoped;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;

import org.jboss.logging.Logger;

@ApplicationScoped
public class TimeTool {

    /**
     * Tool to get the current date-time in a specified time zone.
     */
    private static final Logger LOG = Logger.getLogger(TimeTool.class);

    /**
     * Returns the current date-time in the specified time zone.
     *
     * @param zoneId the ID of the time zone (e.g., "Europe/London")
     * @return the current date-time in ISO format for the specified time zone
     */
    @Tool(description = "Get the current date‑time in a given time zone")
    public String currentTime(
        @ToolArg(description = "Time zone ID (e.g. Europe/London)") String zoneId) {
        
        LOG.infof("Received request for current time in zone: %s", zoneId);
        
        var now = ZonedDateTime.now(java.time.ZoneId.of(zoneId));
        return now.format(DateTimeFormatter.ISO_ZONED_DATE_TIME);
    }
}

