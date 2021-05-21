package com.navex.keycloak.moonwatch.model;

import java.io.Serializable;
import java.util.Date;

public class Session implements Serializable, Cloneable {

    private String id;
    private Date sessionStartUtc;
    private Integer idleTimeoutMinutes;
    private Integer maxTimeoutMinutes;
    private Integer remainingMaxTimeoutExtensions;
    private Date idleTimeout;
    private Date maxTimeout;
    private String logoutUrl;

    public void setId(String value) {
        this.id = value;
    }
    public String getId() {
        return this.id;
    }
    /** @return Returns a reference to this object so that method calls can be chained together. */
    public Session id(String newValue) {
        setId(newValue);
        return this;
    }


    public void setSessionStartUtc(Date value) {
        this.sessionStartUtc = value;
    }
    public Date getSessionStartUtc() {
        return this.sessionStartUtc;
    }
    /** @return Returns a reference to this object so that method calls can be chained together. */
    public Session sesisonStartUtc(Date newValue) {
        setSessionStartUtc(newValue);
        return this;
    }


    public void setIdleTimeoutMinutes(Integer value) {
        this.idleTimeoutMinutes = value;
    }
    public Integer getIdleTimeoutMinutes() {
        return this.idleTimeoutMinutes;
    }
    /** @return Returns a reference to this object so that method calls can be chained together. */
    public Session idleTimeoutMinutes(Integer newValue) {
        setIdleTimeoutMinutes(newValue);
        return this;
    }


    public void setMaxTimeoutMinutes(Integer value) {
        this.maxTimeoutMinutes = value;
    }
    public Integer getMaxTimeoutMinutes() {
        return this.maxTimeoutMinutes;
    }
    public Session maxTimeoutMinutes(Integer newValue) {
        setMaxTimeoutMinutes(newValue);
        return this;
    }


    public void setRemainingMaxTimeoutExtensions(Integer value) {
        this.remainingMaxTimeoutExtensions = value;
    }
    public Integer getRemainingMaxTimeoutExtensions() {
        return this.remainingMaxTimeoutExtensions;
    }
    public Session remainingMaxTimeoutExtensions(Integer newValue) {
        setRemainingMaxTimeoutExtensions(newValue);
        return this;
    }


    public void setIdleTimeout(Date value) {
        this.idleTimeout = value;
    }
    public Date getIdleTimeout() {
        return this.idleTimeout;
    }
    public Session idleTimeout(Date newValue) {
        setIdleTimeout(newValue);
        return this;
    }


    public void setMaxTimeout(Date value) {
        this.maxTimeout = value;
    }
    public Date getMaxTimeout() {
        return this.maxTimeout;
    }
    public Session maxTimeout(Date newValue) {
        setMaxTimeout(newValue);
        return this;
    }


    public void setLogoutUrl(String value) {
        this.logoutUrl = value;
    }
    public String getLogoutUrl() {
        return this.logoutUrl;
    }
    public Session logoutUrl(String newValue) {
        setLogoutUrl(newValue);
        return this;
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        sb.append("{");
        if (getId() != null)
            sb.append("Id: ").append(getId()).append(",");
        sb.append("}");
        return sb.toString();
    }

    @Override
    public boolean equals(Object obj) {
        if (this == obj)
            return true;
        if (obj == null)
            return false;

        if (obj instanceof Session == false)
            return false;
        Session other = (Session) obj;
        if (other.getId() == null ^ this.getId() == null)
            return false;
        if (other.getId() != null && other.getId().equals(this.getId()) == false)
            return false;

        if (other.getSessionStartUtc() == null ^ this.getSessionStartUtc() == null)
            return false;
        if (other.getSessionStartUtc() != null && other.getSessionStartUtc().equals(this.getSessionStartUtc()) == false)
            return false;

        if (other.getIdleTimeoutMinutes() == null ^ this.getIdleTimeoutMinutes() == null)
            return false;
        if (other.getIdleTimeoutMinutes() != null && other.getIdleTimeoutMinutes().equals(this.getIdleTimeoutMinutes()) == false)
            return false;

        if (other.getMaxTimeoutMinutes() == null ^ this.getMaxTimeoutMinutes() == null)
            return false;
        if (other.getMaxTimeoutMinutes() != null && other.getMaxTimeoutMinutes().equals(this.getMaxTimeoutMinutes()) == false)
            return false;

        if (other.getRemainingMaxTimeoutExtensions() == null ^ this.getRemainingMaxTimeoutExtensions() == null)
            return false;
        if (other.getRemainingMaxTimeoutExtensions() != null && other.getRemainingMaxTimeoutExtensions().equals(this.getRemainingMaxTimeoutExtensions()) == false)
            return false;

        if (other.getIdleTimeout() == null ^ this.getIdleTimeout() == null)
            return false;
        if (other.getIdleTimeout() != null && other.getIdleTimeout().equals(this.getIdleTimeout()) == false)
            return false;

        if (other.getMaxTimeout() == null ^ this.getMaxTimeout() == null)
            return false;
        if (other.getMaxTimeout() != null && other.getMaxTimeout().equals(this.getMaxTimeout()) == false)
            return false;

        if (other.getLogoutUrl() == null ^ this.getLogoutUrl() == null)
            return false;
        if (other.getLogoutUrl() != null && other.getLogoutUrl().equals(this.getLogoutUrl()) == false)
            return false;

        return true;
    }

    @Override
    public int hashCode() {
        final int prime = 31;
        int hashCode = 1;

        hashCode = prime * hashCode + ((getId() == null) ? 0 : getId().hashCode());
        hashCode = prime * hashCode + ((getSessionStartUtc() == null) ? 0 : getSessionStartUtc().hashCode());
        hashCode = prime * hashCode + ((getIdleTimeoutMinutes() == null) ? 0 : getIdleTimeoutMinutes().hashCode());
        hashCode = prime * hashCode + ((getMaxTimeoutMinutes() == null) ? 0 : getMaxTimeoutMinutes().hashCode());
        hashCode = prime * hashCode + ((getRemainingMaxTimeoutExtensions() == null) ? 0 : getRemainingMaxTimeoutExtensions().hashCode());
        hashCode = prime * hashCode + ((getIdleTimeout() == null) ? 0 : getIdleTimeout().hashCode());
        hashCode = prime * hashCode + ((getMaxTimeout() == null) ? 0 : getMaxTimeout().hashCode());
        hashCode = prime * hashCode + ((getLogoutUrl() == null) ? 0 : getLogoutUrl().hashCode());
        return hashCode;
    }

    @Override
    public Session clone() {
        try {
            return (Session) super.clone();
        } catch (CloneNotSupportedException e) {
            throw new IllegalStateException("Got a CloneNotSupportedException from Object.clone() " + "even though we're Cloneable!", e);
        }
    }

}
