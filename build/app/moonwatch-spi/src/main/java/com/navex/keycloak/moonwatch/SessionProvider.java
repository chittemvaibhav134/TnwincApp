package com.navex.keycloak.moonwatch;

import com.navex.keycloak.moonwatch.model.InitSessionRequest;
import com.navex.keycloak.moonwatch.model.InitSessionResult;

import org.keycloak.events.*;
import org.keycloak.events.admin.AdminEvent;
import org.keycloak.models.KeycloakSession;

public class SessionProvider implements EventListenerProvider {
    SessionProviderConfig config;
    KeycloakSession session;
    public SessionProvider(SessionProviderConfig config, KeycloakSession session) {
        super();
        this.config = config;
        this.session = session;
    }

    @Override
    public void onEvent(AdminEvent event, boolean includeRepresentation) {
    }

    @Override
    public void onEvent(Event event) {
        if( event.getType() == EventType.LOGIN ) {
            if( config.moonwatchApiBase == null || config.moonwatchApiBase.isEmpty() ) {
                System.err.println( "Unable to handle Moonwatch due to missing base url" );
                return;
            }
            System.out.println("Got LOGIN event from " + event.getSessionId() + " calling Moonwatch InitSession");
            String clientKey = session.getAttribute("clientkey", String.class);
            // check for release toggle
            if( !config.isToggleEnabled("PlatformIdleTimeSettings", clientKey, false) ) {
                System.out.println( "Moonwatch was not notified because PlatformIdleTimeSettings was evaluated to off" );
                return;
            }

            var client = new MoonwatchClientBuilder(event.getSessionId(), config).build();
            try {
                InitSessionRequest request = new InitSessionRequest()
                    .sessionId(event.getSessionId())
                    .keyCloakSessionId(event.getSessionId())
                    .idleTimeout(30)
                    .logoutUrl(null);
                
                InitSessionResult result = client.initSession(request);
                if( result == null ) { return; }
                System.out.println("Moonwatch Session Init: sessionId[" + event.getSessionId() + "] result[" + result.toString() + "]");
            }
            finally {
                client.close();
            }

        }
    }

    @Override
    public void close() {
        
    }
}