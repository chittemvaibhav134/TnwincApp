package com.navex.keycloak.moonwatch.model;

import java.io.Serializable;

public class EndSessionRequest implements Serializable {
    private String id;
    private String reason;

    public void setId(String value) {
        this.id = value;
    }
    public String getId() {
        return this.id;
    }

    public void setReason(String value) {
        this.reason = value;
    }
    public String getReason() {
        return this.reason;
    }

    /** @return Returns a reference to this object so that method calls can be chained together. */
    public EndSessionRequest id(String newId) {
        setId(newId);
        return this;
    }
    /** @return Returns a reference to this object so that method calls can be chained together. */
    public EndSessionRequest reason(String newReason) {
        setReason(newReason);
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
        sb.append("{id: ");
        if (getId() != null)
            sb.append(getId());
        else
            sb.append("null");
        sb.append(" Reason: ")
          .append(getReason())
          .append("}");
        return sb.toString();
    }
}
