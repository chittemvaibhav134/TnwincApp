package com.navex.keycloak.moonwatch;

class Logger {
    public static String messageWithContext(String logContext, String msg) {
        return "[ctx:" + logContext + "] " + msg;
    }
    public static void writeError(String logContext, String msg) {
        System.err.println(messageWithContext(logContext, msg));
    }
    public static void writeInfo(String logContext, String msg) {
        System.out.println(messageWithContext(logContext, msg));
    }
}
