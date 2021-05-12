package com.navex.keycloak.moonwatch;

import java.io.IOException;
import java.util.Map;

import org.keycloak.Config.Scope;
import org.keycloak.events.EventListenerProvider;
import org.keycloak.events.EventListenerProviderFactory;
import org.keycloak.models.KeycloakSession;
import org.keycloak.models.KeycloakSessionFactory;
import com.launchdarkly.sdk.server.*;

public class SessionProviderFactory implements EventListenerProviderFactory{

    SessionProviderConfig serviceConfig;
    LDClient ldClient;

    @Override
    public void close() {
        try {
            ldClient.close();
        }
        catch(IOException ioException) {
            // do nothing... because we're shutting down?
        }
    }

    @Override
    public EventListenerProvider create(KeycloakSession session) {
        return new SessionProvider(serviceConfig, session);
    }

    @Override
    public String getId() {
        return "moonwatch-session-spi";
    }

    @Override
    public void init(Scope arg0) {
        Map<String, String> env = System.getenv();
        
        SessionProviderConfig config = new SessionProviderConfig();
        config.awsRegion = env.get("AWS_REGION");
        config.moonwatchApiBase = env.get("MOONWATCH_API_BASE_URL");

        serviceConfig = config;

        String ldKey = env.get("LAUNCH_DARKLY_KEY");
        if( ldKey != null && !ldKey.isEmpty() ) {
            ldClient = new LDClient(ldKey);
        }
    }

    @Override
    public void postInit(KeycloakSessionFactory arg0) {

    }
    
}
