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
        String clientKey = null;
        if( event.getType() == EventType.LOGIN || event.getType() == EventType.LOGOUT ) {
            if( config.moonwatchApiBase == null || config.moonwatchApiBase.isEmpty() ) {
                Logger.writeError(logContext, "Unable to handle Moonwatch due to missing base url");
                return;
            }
            clientKey = session.getContext().getAuthenticationSession().getAuthenticatedUser().getFirstAttribute("clientkey");
            clientKey = clientKey == null ? "null": clientKey;
            Logger.writeInfo(logContext, "Got " + event.getType() + " event, clientKey: " + clientKey);

            // check for release toggle
            if( !config.isToggleEnabled("PlatformIdleTimeSettings", clientKey, false) ) {
                Logger.writeInfo(logContext, "Moonwatch was not notified because PlatformIdleTimeSettings was evaluated to off");
                return;
            }

            var client = new MoonwatchClientBuilder(event.getSessionId(), config).build();

            try {
                if( event.getType() == EventType.LOGIN ) {
                    InitSessionRequest request = new InitSessionRequest()
                        .sessionId(event.getSessionId())
                        .keyCloakSessionId(event.getSessionId())
                        .idleTimeout(30)
                        .logoutUrl(null);
                    
                    InitSessionResult result = client.initSession(request);
                    if( result == null ) { return; }
                    Logger.writeInfo(logContext, "Moonwatch Session Init: result[" + result.toString() + "]");
                }
                else if( event.getType() == EventType.LOGOUT ) {
                    EndSessionRequest request = new EndSessionRequest()
                        .id(event.getSessionId())
                        .reason("UserInitiated");
                
                    EndSessionResult result = client.endSession(request);
                    if( result == null ) { return; }
                    Logger.writeInfo(logContext, "Moonwatch Session End: result[" + result.toString() + "]");
                }
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