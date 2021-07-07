package com.navex.keycloak.moonwatch.model;

import java.io.Serializable;

public class InitSessionRequest implements Serializable {
    private String sessionId;
    private String keyCloakSessionId = "";
    private String logoutUrl;
    private String clientKey;

    public void setSessionId(String value) {
        this.sessionId = value;
    }
    public String getSessionId() {
        return this.sessionId;
    }

    public void setLogoutUrl(String value) {
        this.logoutUrl = value;
    }
    public String getLogoutUrl() {
        return this.logoutUrl;
    }

    public void setClientKey(String value) {
        this.clientKey = value;
    }
    public String getClientKey() {
        return this.clientKey;
    }

    public void setKeyCloakSessionId(String value) {
        this.keyCloakSessionId = value;
    }
    public String getKeyCloakSessionId() {
        return this.keyCloakSessionId;
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
    public InitSessionRequest clientKey(String newValue) {
        setClientKey(newValue);
        return this;
    }
    public InitSessionRequest keyCloakSessionId(String newValue) {
        setKeyCloakSessionId(newValue);
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
        sb.append(" ClientKey: ")
          .append(getClientKey())
          .append("}");
        return sb.toString();
    }

}
