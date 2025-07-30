package org.pamenon;

import io.quarkus.test.junit.QuarkusTest;
import org.junit.jupiter.api.Test;
import jakarta.inject.Inject;

import static org.junit.jupiter.api.Assertions.*;

@QuarkusTest
public class TimeToolTest {

    @Inject
    TimeTool timeTool; // ✅ Inject your MCP tool bean

    @Test
    public void testCurrentTimeReturnsIsoString() {
        String result = timeTool.currentTime("UTC");

        assertNotNull(result, "TimeTool should return a non-null string");
        assertTrue(result.contains("Z"),
                   "Expected ISO format with a 'Z' indicating UTC timezone");
    }

    @Test
    public void testDifferentTimezone() {
        String result = timeTool.currentTime("Europe/London");

        assertNotNull(result);
        assertTrue(result.contains("+01") || result.contains("+00") || result.contains("[Europe/London]"),
                   "Expected returned string to contain timezone offset or ID");
    }
}
