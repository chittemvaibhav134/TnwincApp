package com.navex.keycloak.moonwatch.model;

import com.amazonaws.opensdk.BaseRequest;
import com.amazonaws.protocol.StructuredPojo;

public class NavexRequest<TPayload extends StructuredPojo> extends BaseRequest {
    private TPayload payload;
    
    public TPayload getPayload() {
        return this.payload;
    }
    public void setPayload(TPayload payload) {
        this.payload = payload;
    }
    public NavexRequest<TPayload> payload(TPayload newPayload) {
        setPayload(newPayload);
        return this;
    }

    /**
     * Set the configuration for this request.
     *
     * @param sdkRequestConfig
     *        Request configuration.
     * @return This object for method chaining.
     */
    public NavexRequest<TPayload> sdkRequestConfig(com.amazonaws.opensdk.SdkRequestConfig sdkRequestConfig) {
        super.sdkRequestConfig(sdkRequestConfig);
        return this;
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        sb.append("{");
        if (getPayload() != null)
            sb.append(getPayload());
        sb.append("}");
        return sb.toString();
    }

    @Override
    public boolean equals(Object obj) {
        if (this == obj)
            return true;
        if (obj == null)
            return false;

        if (obj instanceof NavexRequest<?> == false)
            return false;
        NavexRequest<?> other = (NavexRequest<?>) obj;
        if (other.getPayload() == null ^ this.getPayload() == null)
            return false;
        if (other.getPayload() != null && other.getPayload().equals(this.getPayload()) == false)
            return false;
        return true;
    }

    @Override
    public int hashCode() {
        final int prime = 31;
        int hashCode = 1;

        hashCode = prime * hashCode + ((getPayload() == null) ? 0 : getPayload().hashCode());
        return hashCode;
    }

}
