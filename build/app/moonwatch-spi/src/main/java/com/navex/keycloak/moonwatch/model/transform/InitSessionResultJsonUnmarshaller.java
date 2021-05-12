package com.navex.keycloak.moonwatch.model.transform;

import com.amazonaws.transform.JsonUnmarshallerContext;
import com.amazonaws.transform.Unmarshaller;
import com.navex.keycloak.moonwatch.model.*;

public class InitSessionResultJsonUnmarshaller 
        extends NavexCallResultJsonUnmarshaller<InitSessionResult, Session> {

    @Override
    protected InitSessionResult createFinalType() {
        return new InitSessionResult();
    }

    @Override
    protected Unmarshaller<Session, JsonUnmarshallerContext> getPayloadUnmarshaller(JsonUnmarshallerContext context) {
        return new SessionJsonUnmarshaller();
    }
    
}
