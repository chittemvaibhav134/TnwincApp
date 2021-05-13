package com.navex.keycloak.moonwatch;

import java.net.URI;
import java.util.Map;

import com.amazonaws.Protocol;
import com.amazonaws.annotation.NotThreadSafe;
import com.amazonaws.auth.AWS4Signer;
import com.amazonaws.auth.AWSCredentialsProvider;
import com.amazonaws.auth.AWSStaticCredentialsProvider;
import com.amazonaws.auth.BasicAWSCredentials;
import com.amazonaws.auth.ContainerCredentialsProvider;
import com.amazonaws.auth.RequestSigner;
import com.amazonaws.auth.Signer;
import com.amazonaws.client.AwsSyncClientParams;
import com.amazonaws.opensdk.internal.config.ApiGatewayClientConfigurationFactory;
import com.amazonaws.opensdk.protect.client.SdkSyncClientBuilder;

@NotThreadSafe
public class MoonwatchClientBuilder extends SdkSyncClientBuilder<MoonwatchClientBuilder, MoonwatchClient> {
    private final static String CRED_KEY_ID = "AWS_MW_ACCESS_KEY_ID", CRED_SECRET = "AWS_MW_SECRET_ACCESS_KEY";
    private final String configRegion;

    MoonwatchClientBuilder(SessionProviderConfig config) {
        super(new ApiGatewayClientConfigurationFactory());

        this.configRegion = config.awsRegion;

        AWSCredentialsProvider creds;
        Map<String, String> env = System.getenv();
        if( env.containsKey(CRED_KEY_ID) ) {
            System.out.println("Loading Moonwatch API credentials from the Environment.");
            creds = new AWSStaticCredentialsProvider(new BasicAWSCredentials(env.get(CRED_KEY_ID), env.get(CRED_SECRET)));
        } else {
            System.out.println("Loading Moonwatch API credentials from container session.");
            creds = new ContainerCredentialsProvider();
        }

        this.setEndpoint(config.moonwatchApiBase);
        this.setIamRegion(config.awsRegion);
        this.setIamCredentials(creds);
    }

    @Override
    protected MoonwatchClient build(AwsSyncClientParams clientParams) {
        if( true ) {
            StringBuilder sb = new StringBuilder();
            sb.append("Moonwatch Client Configuration ===");
            sb.append("\nEndPoint: ").append(clientParams.getEndpoint());
            sb.append("\nSigning Provider: ").append(clientParams.getSignerProvider().getClass());
            sb.append("\nCredentials Provider: ").append(clientParams.getCredentialsProvider().getClass());
            // sb.append("").append(clientParams.getMonitoringListener().)

            System.out.println(sb.toString());
        }
        return new MoonwatchClient(clientParams);
    }

    @Override
    protected URI defaultEndpoint() {
        return null;
    }

    @Override
    protected String defaultRegion() {
        return null;
    }

    @Override
    protected MoonwatchClientBuilder signer(RequestSigner requestSigner, Class<? extends RequestSigner> signerType) {
        System.out.println(requestSigner);
        return super.signer(requestSigner, signerType);
    }

    @Override
    protected Signer defaultIamSigner() {
        System.out.println("Did get signer");
        return signerFactory().createSigner();
    }

}
