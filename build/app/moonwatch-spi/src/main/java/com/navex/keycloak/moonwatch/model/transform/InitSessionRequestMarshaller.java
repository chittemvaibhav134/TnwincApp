package com.navex.keycloak.moonwatch.model.transform;

import com.amazonaws.SdkClientException;
import com.navex.keycloak.moonwatch.model.*;

import com.amazonaws.protocol.*;
import com.amazonaws.annotation.SdkInternalApi;

@SdkInternalApi
public class InitSessionRequestMarshaller {
    private static final MarshallingInfo<String> SESSIONID_BINDING = MarshallingInfo.builder(MarshallingType.STRING)
            .marshallLocationName("sessionId").isExplicitPayloadMember(true).build();
    private static final MarshallingInfo<String> LOGOUTURL_BINDING = MarshallingInfo.builder(MarshallingType.STRING)
            .marshallLocationName("logoutUrl").isExplicitPayloadMember(true).build();
    private static final MarshallingInfo<Integer> IDLETIMEOUT_BINDING = MarshallingInfo.builder(MarshallingType.INTEGER)
            .marshallLocationName("idleTimeout").isExplicitPayloadMember(true).build();
    
    private static final InitSessionRequestMarshaller instance = new InitSessionRequestMarshaller();

    public static InitSessionRequestMarshaller getInstance() {
        return instance;
    }

    /**
     * Marshall the given parameter object.
     */
    public void marshall(InitSessionRequest initSessionRequest, ProtocolMarshaller protocolMarshaller) {

        if (initSessionRequest == null) {
            throw new SdkClientException("Invalid argument passed to marshall(...)");
        }

        try {
            System.out.println("Marshalling InitSessionRequest { sessionId: " + initSessionRequest.getSessionId() +
                ", logoutUrl: " + initSessionRequest.getLogoutUrl() +
                ", idleTimeout: " + initSessionRequest.getIdleTimeout() + "}");
            protocolMarshaller.marshall(initSessionRequest.getSessionId(), SESSIONID_BINDING);
            protocolMarshaller.marshall(initSessionRequest.getLogoutUrl(), LOGOUTURL_BINDING);
            protocolMarshaller.marshall(initSessionRequest.getIdleTimeout(), IDLETIMEOUT_BINDING);
        } catch (Exception e) {
            throw new SdkClientException("Unable to marshall request to JSON: " + e.getMessage(), e);
        }
    }
}
