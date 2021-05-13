package com.navex.keycloak.moonwatch.model.transform;

import com.amazonaws.SdkClientException;
import com.amazonaws.protocol.MarshallLocation;
import com.amazonaws.protocol.MarshallingInfo;
import com.amazonaws.protocol.MarshallingType;
import com.amazonaws.protocol.ProtocolMarshaller;
import com.amazonaws.protocol.StructuredPojo;
import com.navex.keycloak.moonwatch.model.NavexRequest;

public class NavexRequestMarshaller<TPayload extends StructuredPojo> {
    private static final MarshallingInfo<StructuredPojo> PAYLOAD_BINDING = MarshallingInfo.builder(MarshallingType.STRUCTURED)
            .marshallLocation(MarshallLocation.PAYLOAD).isExplicitPayloadMember(true).build();

    /**
     * Marshall the given parameter object.
     */
    public void marshall(NavexRequest<TPayload> request, ProtocolMarshaller protocolMarshaller) {

        if (request == null) {
            throw new SdkClientException("Invalid argument passed to marshall(...)");
        }

        try {
            protocolMarshaller.marshall(request.getPayload(), PAYLOAD_BINDING);
        } catch (Exception e) {
            throw new SdkClientException("Unable to marshall request to JSON: " + e.getMessage(), e);
        }
    }


}
