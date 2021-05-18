package com.navex.keycloak.moonwatch;

import java.io.IOException;
import java.nio.charset.StandardCharsets;

import com.navex.keycloak.moonwatch.model.*;

import software.amazon.awssdk.auth.credentials.AwsCredentialsProvider;
import software.amazon.awssdk.auth.signer.AwsSignerExecutionAttribute;
import software.amazon.awssdk.awscore.client.config.AwsClientOption;
import software.amazon.awssdk.core.ClientType;
import software.amazon.awssdk.core.client.config.SdkAdvancedClientOption;
import software.amazon.awssdk.core.client.config.SdkClientConfiguration;
import software.amazon.awssdk.core.client.config.SdkClientOption;
import software.amazon.awssdk.core.interceptor.ExecutionAttributes;
import software.amazon.awssdk.core.signer.Signer;
import software.amazon.awssdk.core.util.json.JacksonUtils;
import software.amazon.awssdk.http.HttpExecuteRequest;
import software.amazon.awssdk.http.HttpExecuteResponse;
import software.amazon.awssdk.http.SdkHttpClient;
import software.amazon.awssdk.http.SdkHttpFullRequest;
import software.amazon.awssdk.http.SdkHttpMethod;


public class MoonwatchClient implements AutoCloseable {
    private SdkClientConfiguration config;
    private AwsCredentialsProvider credentialsProvider;
    private SdkHttpClient httpClient;
    private Signer signer;
    private String logContext;

    String messageWithContext(String msg) {
        return Logger.messageWithContext(logContext, msg);
    }
    void writeError(String msg) {
        Logger.writeError(logContext, msg);
    }

    public MoonwatchClient(String logContext, SdkClientConfiguration config) {
        this.logContext = logContext;
        this.config = config;
        if( config.option(SdkClientOption.CLIENT_TYPE) == ClientType.ASYNC ) throw MoonwatchException.create(messageWithContext("Async Client Types are not supported"));

        httpClient = config.option(SdkClientOption.SYNC_HTTP_CLIENT);
        if( httpClient == null ) throw MoonwatchException.create(messageWithContext("Unable to get HTTPClient from SdkClientConfiguration"));

        credentialsProvider = config.option(AwsClientOption.CREDENTIALS_PROVIDER);
        if( credentialsProvider == null ) throw MoonwatchException.create(messageWithContext("Unable to get CredentialsProvider from SdkClientConfiguration"));

        signer = config.option(SdkAdvancedClientOption.SIGNER);
        if( signer == null ) throw MoonwatchException.create(messageWithContext("Unable to get Signer from SdkClientConfiguration"));
    }

    private SdkHttpFullRequest buildRequest(SdkHttpMethod method, String path, Object bodyObj) {
        return SdkHttpFullRequest.builder()
            .method(method)
            .uri(config.option(SdkClientOption.ENDPOINT))
            .encodedPath(path)
            .contentStreamProvider(new JsonContentStream(bodyObj))
            .putHeader("Accept", "application/json")
            .putHeader("Content-type", "application/json")
            .build();
    }
    
    private SdkHttpFullRequest signRequest(SdkHttpFullRequest request) {
        var creds = credentialsProvider.resolveCredentials();
        var signingName = config.option(AwsClientOption.SERVICE_SIGNING_NAME);
        var region = config.option(AwsClientOption.AWS_REGION);

        var exeAttrs = ExecutionAttributes.builder()
            .put(AwsSignerExecutionAttribute.AWS_CREDENTIALS, creds)
            .put(AwsSignerExecutionAttribute.SERVICE_SIGNING_NAME, signingName)
            .put(AwsSignerExecutionAttribute.SIGNING_REGION, region)
            .build();
        
        return signer.sign(request, exeAttrs);
    }

    private HttpExecuteResponse executeRequest(SdkHttpFullRequest request) {
        var exeRequest = HttpExecuteRequest.builder()
            .request(request)
            .contentStreamProvider(request.contentStreamProvider().get())
            .build();

        var doRequest = httpClient.prepareRequest(exeRequest);
        try {
            return doRequest.call();
        }
        catch(IOException ex) {
            throw MoonwatchException.create(messageWithContext("Unable to make call to " + request.encodedPath()), ex);
        }
    }

    private <T> T handleResponse(String requestPath, HttpExecuteResponse response, Class<T> clazz) {
        try {
            var sdkResponse = response.httpResponse();
            var body = response.responseBody();
            if( sdkResponse.isSuccessful() ) {
                String s = new String(body.get().readAllBytes(), StandardCharsets.UTF_8);
                return JacksonUtils.fromJsonString(s, clazz);
            } else {
                if( body.isPresent() ) {
                    String s = new String(body.get().readAllBytes(), StandardCharsets.UTF_8);
                    writeError("Got failed call to " + requestPath + " resulted in " + sdkResponse.statusCode() + " with responseBody: " + s.substring(0, Math.min(512, s.length())));
                    return null;
                }
                else {
                    writeError("Got failed call to " + requestPath + " resulted in " + sdkResponse.statusCode() + " " + sdkResponse.statusText());
                    return null;
                }
            }
        }
        catch(IOException ex) {
            throw MoonwatchException.create(messageWithContext("Exception while reading resposne to " + requestPath), ex);
        }
    }

    public InitSessionResult initSession(InitSessionRequest request) throws MoonwatchException {
        String path = "/v1/session/init";
        
        var sdkRequest = signRequest(buildRequest(SdkHttpMethod.POST, path, request));
        var response = executeRequest(sdkRequest);
        return handleResponse(path, response, InitSessionResult.class);
    }

    public EndSessionResult endSession(EndSessionRequest request) throws MoonwatchException {
        String path = "/v1/session/end";
        
        var sdkRequest = signRequest(buildRequest(SdkHttpMethod.POST, path, request));
        var response = executeRequest(sdkRequest);
        return handleResponse(path, response, EndSessionResult.class);
    }

    @Override
    public void close() {
        if( httpClient != null ) {
            httpClient.close();
        }
    }
}
