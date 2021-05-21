package com.navex.keycloak.moonwatch.model;

import software.amazon.awssdk.core.exception.SdkClientException;

/**
 * Base exception for all service exceptions thrown by PetStore
 */
public class MoonwatchException extends SdkClientException {
    public static MoonwatchException create(String message) {
        return new MoonwatchException(SdkClientException.builder().message(message));
    }
    public static MoonwatchException create(String message, Throwable cause) {
        return new MoonwatchException(SdkClientException.builder().message(message).cause(cause));
    }

    MoonwatchException(Builder b) {
        super(b);
    }
}
