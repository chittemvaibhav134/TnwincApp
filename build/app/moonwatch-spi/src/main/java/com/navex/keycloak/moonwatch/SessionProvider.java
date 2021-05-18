package com.navex.keycloak.moonwatch;

import com.navex.keycloak.moonwatch.model.*;

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
        String logContext = event.getSessionId();
        if( event.getType() == EventType.LOGIN ) {
            if( config.moonwatchApiBase == null || config.moonwatchApiBase.isEmpty() ) {
                Logger.writeError(logContext, "Unable to handle Moonwatch due to missing base url");
                return;
            }
            Logger.writeInfo(logContext, "Got LOGIN event, calling Moonwatch InitSession");
            String clientKey = session.getAttribute("clientkey", String.class);
            // check for release toggle
            if( !config.isToggleEnabled("PlatformIdleTimeSettings", clientKey, false) ) {
                Logger.writeInfo(logContext, "Moonwatch was not notified because PlatformIdleTimeSettings was evaluated to off");
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
                Logger.writeInfo(logContext, "Moonwatch Session Init: result[" + result.toString() + "]");
            }
            finally {
                client.close();
            }
        }
        else if( event.getType() == EventType.LOGOUT ) {
            if( config.moonwatchApiBase == null || config.moonwatchApiBase.isEmpty() ) {
                Logger.writeError(logContext, "Unable to handle Moonwatch due to missing base url");
                return;
            }
            Logger.writeInfo(logContext, "Got LOGOUT event, calling Moonwatch EndSession");
            String clientKey = session.getAttribute("clientkey", String.class);
            // check for release toggle
            if( !config.isToggleEnabled("PlatformIdleTimeSettings", clientKey, false) ) {
                Logger.writeInfo(logContext, "Moonwatch was not notified because PlatformIdleTimeSettings was evaluated to off" );
                return;
            }

            var client = new MoonwatchClientBuilder(event.getSessionId(), config).build();

            EndSessionRequest request = new EndSessionRequest()
                .id(event.getSessionId())
                .reason("UserInitiated");
        
            EndSessionResult result = client.endSession(request);
            if( result == null ) { return; }
            Logger.writeInfo(logContext, "Moonwatch Session End: result[" + result.toString() + "]");

            client.close();
            client = null;

        }
    }

    @Override
    public void close() {

    }
}