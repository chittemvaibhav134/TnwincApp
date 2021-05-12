package com.navex.keycloak.moonwatch.model.transform;

import com.navex.keycloak.moonwatch.model.*;
import com.amazonaws.transform.*;

import com.fasterxml.jackson.core.JsonToken;
import static com.fasterxml.jackson.core.JsonToken.*;

public abstract class NavexCallResultJsonUnmarshaller<ResultType extends NavexCallResult<PayloadType>, PayloadType>
        implements Unmarshaller<ResultType, JsonUnmarshallerContext> {

    
    protected abstract ResultType createFinalType();

    protected abstract Unmarshaller<PayloadType, JsonUnmarshallerContext> getPayloadUnmarshaller(JsonUnmarshallerContext context);

    public ResultType unmarshall(JsonUnmarshallerContext context) throws Exception {
        ResultType result = createFinalType();

        int originalDepth = context.getCurrentDepth();
        String currentParentElement = context.getCurrentParentElement();
        int targetDepth = originalDepth + 1;

        JsonToken token = context.getCurrentToken();
        if (token == null)
            token = context.nextToken();
        if (token == VALUE_NULL) {
            return result;
        }

        while (true) {
            if (token == null)
                break;

            if (token == FIELD_NAME || token == START_OBJECT) {
                if (context.testExpression("status", targetDepth)) {
                    context.nextToken();
                    result.setStatus(context.getUnmarshaller(ResultStatus.class).unmarshall(context));
                }
                if (context.testExpression("sessionStartUtc", targetDepth)) {
                    context.nextToken();
                    result.setErrors(context.getUnmarshaller(String[].class).unmarshall(context));
                }
                if (context.testExpression("idleTimeoutMinutes", targetDepth)) {
                    context.nextToken();
                    result.setData(getPayloadUnmarshaller(context).unmarshall(context));
                }
            } else if (token == END_ARRAY || token == END_OBJECT) {
                if (context.getLastParsedParentElement() == null || context.getLastParsedParentElement().equals(currentParentElement)) {
                    if (context.getCurrentDepth() <= originalDepth)
                        break;
                }
            }

            token = context.nextToken();
        }

        return result;
    }
}
