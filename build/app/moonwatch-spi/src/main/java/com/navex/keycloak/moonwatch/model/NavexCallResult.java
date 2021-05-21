package com.navex.keycloak.moonwatch.model;

import java.io.Serializable;

public class NavexCallResult<PayloadType> implements Serializable, Cloneable {
    private ResultStatus status;
    private PayloadType data;
    private String[] errors;

    public void setStatus(ResultStatus value) {
        this.status = value;
    }
    public ResultStatus getStatus() {
        return this.status;
    }
    public NavexCallResult<PayloadType> status(ResultStatus newValue) {
        setStatus(newValue);
        return this;
    }


    public void setData(PayloadType value) {
        this.data = value;
    }
    public PayloadType getData() {
        return this.data;
    }
    public NavexCallResult<PayloadType> data(PayloadType newValue) {
        setData(newValue);
        return this;
    }


    public void setErrors(String[] value) {
        this.errors = value;
    }
    public String[] getErrors() {
        return this.errors;
    }
    public NavexCallResult<PayloadType> errors(String[] newValue) {
        setErrors(newValue);
        return this;
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        sb.append("{ ");
        sb.append("status: ").append(getStatus());
        if( getStatus() == ResultStatus.success ) {
            sb.append(", data: ");
            if( getData() == null ) sb.append("null");
            else sb.append(getData().toString());
        } else {
            sb.append(", errors: ").append(String.join(",", getErrors()));
        }
        sb.append(" }");
        return sb.toString();
    }
}
