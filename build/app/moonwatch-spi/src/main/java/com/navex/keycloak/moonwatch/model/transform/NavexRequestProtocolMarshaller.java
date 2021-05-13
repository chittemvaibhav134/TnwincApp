package com.navex.keycloak.moonwatch.model.transform;

import com.amazonaws.SdkClientException;
import com.amazonaws.Request;

import com.amazonaws.http.HttpMethodName;
import com.navex.keycloak.moonwatch.model.*;

import com.amazonaws.protocol.*;
import com.amazonaws.protocol.Protocol;
import com.amazonaws.transform.Marshaller;
import com.amazonaws.annotation.SdkInternalApi;

@SdkInternalApi
public class NavexRequestProtocolMarshaller<TPayload extends StructuredPojo> implements Marshaller<Request<NavexRequest<TPayload>>, NavexRequest<TPayload>> {
    private static final OperationInfo SDK_OPERATION_BINDING = OperationInfo.builder().protocol(Protocol.API_GATEWAY)
            .requestUri("/v1/session/init").httpMethodName(HttpMethodName.POST).hasExplicitPayloadMember(true)
            .hasPayloadMembers(true).serviceName("Moonwatch").build();

    private final com.amazonaws.opensdk.protect.protocol.ApiGatewayProtocolFactoryImpl protocolFactory;

    public NavexRequestProtocolMarshaller(com.amazonaws.opensdk.protect.protocol.ApiGatewayProtocolFactoryImpl protocolFactory) {
        this.protocolFactory = protocolFactory;
    }

    public Request<NavexRequest<TPayload>> marshall(NavexRequest<TPayload> initSessionRequest) {

        if (initSessionRequest == null) {
            throw new SdkClientException("Invalid argument passed to marshall(...)");
        }

        try {
            final ProtocolRequestMarshaller<NavexRequest<TPayload>> protocolMarshaller = protocolFactory
                    .createProtocolMarshaller(SDK_OPERATION_BINDING, initSessionRequest);

            protocolMarshaller.startMarshalling();
            new NavexRequestMarshaller<TPayload>().marshall(initSessionRequest, protocolMarshaller);
            return protocolMarshaller.finishMarshalling();
        } catch (Exception e) {
            System.err.println(e.getCause().getMessage());
            throw new SdkClientException("Unable to marshall request to JSON: " + e.getMessage(), e);
        }
    }

}
