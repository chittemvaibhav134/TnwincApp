/**
 * text
 */
package com.navex.keycloak.moonwatch.model.transform;

import java.util.Date;

import com.navex.keycloak.moonwatch.model.*;
import com.amazonaws.transform.*;

import com.fasterxml.jackson.core.JsonToken;
import static com.fasterxml.jackson.core.JsonToken.*;

/**
 * Session JSON Unmarshaller
 */
public class SessionJsonUnmarshaller implements Unmarshaller<Session, JsonUnmarshallerContext> {

    public Session unmarshall(JsonUnmarshallerContext context) throws Exception {
        Session session = new Session();

        int originalDepth = context.getCurrentDepth();
        String currentParentElement = context.getCurrentParentElement();
        int targetDepth = originalDepth + 1;

        JsonToken token = context.getCurrentToken();
        if (token == null)
            token = context.nextToken();
        if (token == VALUE_NULL) {
            return null;
        }

        while (true) {
            if (token == null)
                break;

            if (token == FIELD_NAME || token == START_OBJECT) {
                if (context.testExpression("id", targetDepth)) {
                    context.nextToken();
                    session.setId(context.getUnmarshaller(String.class).unmarshall(context));
                }
                if (context.testExpression("sessionStartUtc", targetDepth)) {
                    context.nextToken();
                    session.setSessionStartUtc(context.getUnmarshaller(Date.class).unmarshall(context));
                }
                if (context.testExpression("idleTimeoutMinutes", targetDepth)) {
                    context.nextToken();
                    session.setIdleTimeoutMinutes(context.getUnmarshaller(Integer.class).unmarshall(context));
                }
                if (context.testExpression("maxTimeoutMinutes", targetDepth)) {
                    context.nextToken();
                    session.setMaxTimeoutMinutes(context.getUnmarshaller(Integer.class).unmarshall(context));
                }
                if (context.testExpression("remainingMaxTimeoutExtensions", targetDepth)) {
                    context.nextToken();
                    session.setRemainingMaxTimeoutExtensions(context.getUnmarshaller(Integer.class).unmarshall(context));
                }
                if (context.testExpression("idleTimeout", targetDepth)) {
                    context.nextToken();
                    session.setIdleTimeout(context.getUnmarshaller(Date.class).unmarshall(context));
                }
                if (context.testExpression("maxTimeout", targetDepth)) {
                    context.nextToken();
                    session.setIdleTimeout(context.getUnmarshaller(Date.class).unmarshall(context));
                }
                if (context.testExpression("logoutUrl", targetDepth)) {
                    context.nextToken();
                    session.logoutUrl(context.getUnmarshaller(String.class).unmarshall(context));
                }
            } else if (token == END_ARRAY || token == END_OBJECT) {
                if (context.getLastParsedParentElement() == null || context.getLastParsedParentElement().equals(currentParentElement)) {
                    if (context.getCurrentDepth() <= originalDepth)
                        break;
                }
            }
            token = context.nextToken();
        }

        return session;
    }

    private static SessionJsonUnmarshaller instance;

    public static SessionJsonUnmarshaller getInstance() {
        if (instance == null)
            instance = new SessionJsonUnmarshaller();
        return instance;
    }
}
