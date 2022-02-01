import { JwksClient } from 'jwks-rsa';
import { decode as jwtdecode, verify as jwtverify } from 'jsonwebtoken';
import { APIGatewayAuthorizerEvent, APIGatewayRequestAuthorizerEvent, APIGatewayRequestAuthorizerEventV2, PolicyDocument } from 'aws-lambda';
import { areAllElementsStrings } from './util';
import { verifyScope } from './scope';
import { NavexJwt, NavexJwtPayload } from './navexjwts';

/** Creates an IAM PolicyDocument from the given parameters. */
const getPolicyDocument = (effect: string, resource: string): PolicyDocument => {
    const policyDocument = {
        Version: '2012-10-17', // default version
        Statement: [{
            Action: 'execute-api:Invoke', // default action
            Effect: effect,
            Resource: resource,
        }]
    };
    return policyDocument;
}

/** Extract and return the Bearer Token from the Lambda event parameters */
const getToken = (params: APIGatewayAuthorizerEvent): string => {
    const eventType = params.type;

    if (eventType === 'TOKEN') {
        const tokenString = params.authorizationToken;
        if (!tokenString) {
            throw new Error('Expected "event.authorizationToken" parameter to be set');
        }
        return getRequestToken(tokenString);
    } else if (eventType === 'REQUEST') {
        const headers = params.headers;
        if (!headers) {
            throw new Error('Expected "event.headers" parameter to be set');
        }
        if (headers.Connection === "upgrade" && headers.Upgrade === "websocket") {
            return getWebSocketRequestToken(params);
        } else {
            const tokenString = headers["authorization"];
            return getRequestToken(tokenString);
        }
    } else {
        throw new Error('Expected "event.type" parameter to have value "TOKEN" or "REQUEST"');
    }
}

/**
 * @returns {string} The raw values of the Bearer Authorization
 */
const getRequestToken = (tokenString: string): string => {
    const match = tokenString.match(/^Bearer (.*)$/);
    if (!match || match.length < 2) {
        throw new Error(`Invalid Authorization token - ${tokenString} does not match "Bearer .*"`);
    }
    return match[1];
}

/**
 * @returns The Bearer token from a WebSocket request
 */
const getWebSocketRequestToken = (request: APIGatewayRequestAuthorizerEvent): string => {
    const headers = request.headers;
    if (!headers) {
        throw new Error('Expected "event.headers" parameter to be set');
    }

    const subProtocolHeader = headers['Sec-WebSocket-Protocol'];
    const subProtocols = subProtocolHeader.split(',');
    const match = subProtocols[0].match(/^bearer(.*)$/);
    if (!match || match.length < 2) {
        throw new Error('Invalid sub protocol.');
    }
    return match[1];
}

const getClientKey = (decodedToken: NavexJwt): string => {
    if (!decodedToken.payload || !decodedToken.payload.clientkey) {
        throw new Error('token does not have clientkey')
    }
    return decodedToken.payload.clientkey
}

function buildJwksUriFromIssuer(token: NavexJwt): string {
    if (!token.payload.iss) { throw new Error('invalid issuer') }
    const jwksTemplate = process.env.JWKS_URI
    const jwksHostname = new URL(jwksTemplate).hostname
    const issuerHostname = new URL(token.payload.iss).hostname
    if(jwksHostname.replace('*.', '') == issuerHostname) {
        return jwksTemplate.replace('*.', '');
    } else {
        const clientKey = getClientKey(token);
        return jwksTemplate.replace('*', clientKey)
    }
}

const jwksClients = new Map<string, JwksClient>();
function getJwksClient(token: NavexJwt): JwksClient {
    
    const jwksUri = buildJwksUriFromIssuer(token);
    const client = jwksClients.get(jwksUri)
    if (client === undefined) {
        const newClient = new JwksClient({
            cache: true,
            rateLimit: true,
            jwksRequestsPerMinute: 10, // Default value
            jwksUri: jwksUri,
        });
        jwksClients.set(jwksUri, newClient);
        return newClient;
    } else {
        return client;
    }
}

function getMethodArn(authorizerEvent: APIGatewayAuthorizerEvent): string {
    if (authorizerEvent.type == 'REQUEST') {
        // test for a V2 request structure, if it is, then use routeArn over methodArn
        const authEventV2 = <APIGatewayRequestAuthorizerEventV2><unknown>authorizerEvent;
        if ( authEventV2.version ) { return authEventV2.routeArn; }
        else { return authorizerEvent.methodArn; }
    }
    else if (!authorizerEvent.methodArn) { throw new Error('authorizerEvent.methodArn must be set') }
    else { return authorizerEvent.methodArn; }
}
/**
 * 
 * @param {*} authorizerEvent 
 * @returns 
 */
export async function authenticateToken(authorizerEvent: APIGatewayAuthorizerEvent, audiences: string[], scopes: string[] ) {
    if (!authorizerEvent) { throw new Error('authorizerEvent is required and should match APIGatewayAuthorizerEvent') }
    if (!Array.isArray(audiences)) { throw new Error('audience is required and must be an array') }
    if (!Array.isArray(scopes)) { throw new Error('scopes is required and must be an array') }
    
    if (audiences.length == 0) { throw new Error('audiences cannot be an empty array') }
    if (scopes.length == 0) { throw new Error('scopes cannot be an empty array') }
    
    if (!areAllElementsStrings(audiences)) { throw new Error('all elements of audience must be of type string') }
    if (!areAllElementsStrings(scopes)) { throw new Error('all elements of scopes must be of type string') }
    
    const methodArn = getMethodArn(authorizerEvent);

    const token = getToken(authorizerEvent)

    const decoded = <NavexJwt>jwtdecode(token, { complete: true })
    if (!decoded || !decoded.header || !decoded.header.kid) {
        throw new Error('invalid token')
    }
    const { payload } = decoded
    if (!payload) {
        throw new Error('invalid token payload')
    }
    
    verifyScope(scopes, payload.scope);

    const client = getJwksClient(decoded);

    const key = await client.getSigningKey(decoded.header.kid);
    const signingKey = key.getPublicKey();
    const verifiedPayload = <NavexJwtPayload>jwtverify(token, signingKey, { audience: audiences });
    return ({
        principalId: verifiedPayload.sub,
        policyDocument: getPolicyDocument('Allow', methodArn),
        context: { scope: verifiedPayload.scope, session_state: verifiedPayload.session_state, clientkey: verifiedPayload.clientkey }
    });
}
