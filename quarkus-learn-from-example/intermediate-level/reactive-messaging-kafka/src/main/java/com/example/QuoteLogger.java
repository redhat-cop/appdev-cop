package com.example;

import jakarta.enterprise.context.ApplicationScoped;
import org.eclipse.microprofile.reactive.messaging.Incoming;
import org.jboss.logging.Logger;

@ApplicationScoped
public class QuoteLogger {

    private static final Logger LOG = Logger.getLogger(QuoteLogger.class);

    @Incoming("quotes-in")
    public void consume(Quote quote) {
        LOG.infof("Received quote from %s: \"%s\"", quote.author, quote.text);
    }
}
