package com.navex.keycloak.moonwatch;

import java.util.Arrays;

import com.amazonaws.SdkBaseException;
import com.amazonaws.annotation.ThreadSafe;
import com.amazonaws.client.AwsSyncClientParams;
import com.amazonaws.client.ClientExecutionParams;
import com.amazonaws.client.ClientHandler;
import com.amazonaws.client.ClientHandlerParams;
import com.amazonaws.http.HttpResponseHandler;
import com.amazonaws.opensdk.protect.client.SdkClientHandler;
import com.amazonaws.protocol.json.JsonClientMetadata;
import com.amazonaws.protocol.json.JsonErrorResponseMetadata;
import com.amazonaws.protocol.json.JsonErrorShapeMetadata;
import com.amazonaws.protocol.json.JsonOperationMetadata;
import com.navex.keycloak.moonwatch.model.*;
import com.navex.keycloak.moonwatch.model.transform.*;

@ThreadSafe
public class MoonwatchClient {
    private final ClientHandler clientHandler;

    private static final com.amazonaws.opensdk.protect.protocol.ApiGatewayProtocolFactoryImpl protocolFactory = 
        new com.amazonaws.opensdk.protect.protocol.ApiGatewayProtocolFactoryImpl(
            new JsonClientMetadata()
                .withProtocolVersion("1.1")
                .withSupportsCbor(false)
                .withSupportsIon(false)
                .withContentTypeOverride("application/json")
                .withBaseServiceExceptionClass(com.navex.keycloak.moonwatch.model.MoonwatchException.class));
    
    public MoonwatchClient(AwsSyncClientParams clientParams) {
        this.clientHandler = new SdkClientHandler(new ClientHandlerParams().withClientParams(clientParams));
    }

    public InitSessionResult initSession(InitSessionRequest request) {
        HttpResponseHandler<InitSessionResult> responseHandler = protocolFactory
            .createResponseHandler(
                new JsonOperationMetadata()
                    .withPayloadJson(true)
                    .withHasStreamingSuccessResponse(false),
                new InitSessionResultJsonUnmarshaller()
            );

        HttpResponseHandler<SdkBaseException> errorResponseHandler = createErrorResponseHandler();

        return clientHandler.execute(new ClientExecutionParams<InitSessionRequest, InitSessionResult>()
                .withMarshaller(new InitSessionRequestProtocolMarshaller(protocolFactory))
                .withResponseHandler(responseHandler)
                .withErrorResponseHandler(errorResponseHandler)
                .withInput(request));
    }

    /**
     * Create the error response handler for the operation.
     * 
     * @param errorShapeMetadata
     *        Error metadata for the given operation
     * @return Configured error response handler to pass to HTTP layer
     */
    private HttpResponseHandler<SdkBaseException> createErrorResponseHandler(JsonErrorShapeMetadata... errorShapeMetadata) {
        return protocolFactory.createErrorResponseHandler(new JsonErrorResponseMetadata().withErrorShapes(Arrays.asList(errorShapeMetadata)));
    }

    public void shutdown() {
        clientHandler.shutdown();
    }
}
