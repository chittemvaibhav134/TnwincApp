package com.navex.keycloak.moonwatch.model;

public class InitSessionRequest extends com.amazonaws.opensdk.BaseRequest {
    private String sessionId;
    public void setSessionId(String value) {
        this.sessionId = value;
    }
    public String getSessionId() {
        return this.sessionId;
    }

    private String logoutUrl;
    public void setLogoutUrl(String value) {
        this.logoutUrl = value;
    }
    public String getLogoutUrl() {
        return this.logoutUrl;
    }

    private Integer idleTimeout;
    public void setIdleTimeout(Integer value) {
        this.idleTimeout = value;
    }
    public Integer getIdleTimeout() {
        return this.idleTimeout;
    }

    /** @return Returns a reference to this object so that method calls can be chained together. */
    public InitSessionRequest sessionId(String newSessionId) {
        setSessionId(newSessionId);
        return this;
    }
    /** @return Returns a reference to this object so that method calls can be chained together. */
    public InitSessionRequest logoutUrl(String newLogoutUrl) {
        setLogoutUrl(newLogoutUrl);
        return this;
    }
    /** @return Returns a reference to this object so that method calls can be chained together. */
    public InitSessionRequest idleTimeout(int newidleTimeout) {
        setIdleTimeout(newidleTimeout);
        return this;
    }

    /**
     * Returns a string representation of this object. This is useful for testing and debugging. Sensitive data will be
     * redacted from this string using a placeholder value.
     *
     * @return A string representation of this object.
     *
     * @see java.lang.Object#toString()
     */
    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        sb.append("{SessionId: ");
        if (getSessionId() != null)
            sb.append(getSessionId());
        else
            sb.append("null");
        sb.append(" IdleTimeout: ")
          .append(getIdleTimeout())
          .append("}");
        return sb.toString();
    }

    @Override
    public boolean equals(Object obj) {
        if (this == obj)
            return true;
        if (obj == null)
            return false;

        if (obj instanceof InitSessionRequest == false)
            return false;
        InitSessionRequest other = (InitSessionRequest) obj;
        if (other.getIdleTimeout() != this.getIdleTimeout() )
            return false;
        if (other.getSessionId() == null ^ this.getSessionId() == null)
            return false;
        if (other.getLogoutUrl() == null ^ this.getLogoutUrl() == null)
            return false;
        if (other.getSessionId() != null && other.getSessionId().equals(this.getSessionId()) == false)
            return false;
        if (other.getLogoutUrl() != null && other.getLogoutUrl().equals(this.getLogoutUrl()) == false)
            return false;
        return true;
    }

    @Override
    public int hashCode() {
        final int prime = 31;
        int hashCode = 1;

        hashCode = prime * hashCode + ((getSessionId() == null) ? 0 : getSessionId().hashCode());
        hashCode = prime * hashCode + ((getLogoutUrl() == null) ? 0 : getLogoutUrl().hashCode());
        hashCode = prime * hashCode + ((getIdleTimeout() == null) ? 0 : getIdleTimeout().hashCode());
        
        return hashCode;
    }

    @Override
    public InitSessionRequest clone() {
        return (InitSessionRequest) super.clone();
    }

    /**
     * Set the configuration for this request.
     *
     * @param sdkRequestConfig
     *        Request configuration.
     * @return This object for method chaining.
     */
    public InitSessionRequest sdkRequestConfig(com.amazonaws.opensdk.SdkRequestConfig sdkRequestConfig) {
        super.sdkRequestConfig(sdkRequestConfig);
        return this;
    }
}