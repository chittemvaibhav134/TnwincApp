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
        var eventType = event.getType();
        var userId = event.getUserId();
        if( eventType == EventType.LOGIN || eventType == EventType.LOGOUT ) {
            if( config.moonwatchApiBase == null || config.moonwatchApiBase.isEmpty() ) {
                Logger.writeError(logContext, "Unable to handle Moonwatch due to missing base url");
                return;
            }

            var userDb = session.users();
            var sessionContext = session.getContext();
            if( sessionContext == null ) {
                Logger.writeError(logContext, "Session lacked Context, unable to process due to missing ClientKey");
                return;
            }

            Logger.writeInfo(logContext, "userId:" + userId);
            var user = userDb.getUserById(userId, sessionContext.getRealm());

            clientKey = user.getFirstAttribute("clientkey");

            Logger.writeInfo(logContext, "Got " + eventType + " event, clientKey: " + clientKey);

            // check for release toggle
            if( !config.isToggleEnabled("PlatformIdleTimeSettings", clientKey, false) ) {
                Logger.writeInfo(logContext, "Moonwatch was not notified because PlatformIdleTimeSettings was evaluated to off");
                return;
            }

            var client = new MoonwatchClientBuilder(event.getSessionId(), config).build();

            try {
                if( eventType == EventType.LOGIN ) {
                    InitSessionRequest request = new InitSessionRequest()
                        .sessionId(event.getSessionId())
                        .keyCloakSessionId(event.getSessionId())
                        .clientKey(clientKey)
                        .logoutUrl(null);

                    InitSessionResult result = client.initSession(request);
                    if( result == null ) { return; }
                    Logger.writeInfo(logContext, "Moonwatch Session Init: result[" + result.toString() + "]");
                }
                else if( eventType == EventType.LOGOUT ) {
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
