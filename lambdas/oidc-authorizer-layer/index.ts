import { JwksClient } from 'jwks-rsa';
import { decode as jwtdecode, verify as jwtverify } from 'jsonwebtoken';
import { APIGatewayAuthorizerEvent, APIGatewayRequestAuthorizerEvent, APIGatewayRequestAuthorizerEventV2, PolicyDocument } from 'aws-lambda';
import { isStringArray } from './util';
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
const getToken = (params: IAPIGatewayAuthorizerEventSubsetNeededForAuthenicateToken): string => {
    const eventType = params.type;

    if (eventType === 'TOKEN') {
        return getRequestToken(params.authorizationToken);
    } else {
        const headers = params.headers;
        if (headers.Connection === "upgrade" && headers.Upgrade === "websocket") {
            return getWebSocketRequestToken(params);
        } else {
            return getRequestToken(headers.authorization);
        }
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
const getWebSocketRequestToken = (request: IRequestV1AuthEvent|IRequestV2AuthEvent): string => {
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
    if (!decodedToken?.payload?.clientkey) {
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

function getMethodArn(authorizerEvent: IAPIGatewayAuthorizerEventSubsetNeededForAuthenicateToken): string {
    if (isRequestV2(authorizerEvent)) { return authorizerEvent.routeArn; }
    else { return authorizerEvent.methodArn; }
}

interface ITokenAuthEvent {
     type: "TOKEN";
     methodArn: string;
     authorizationToken: string;
}
function isTokenEvent(event: any): event is ITokenAuthEvent {
    return typeof(event) === 'object' &&
        event.type === 'TOKEN' &&
        typeof(event.methodArn) === 'string' &&
        typeof(event.authorizationToken) === 'string';
}
interface IRequestAuthEventCommonFields {
    type: "REQUEST";
    headers: {
        [key: string]: string;
    };
}
function isRequestAuthEvent(event: any): event is IRequestAuthEventCommonFields {
    return typeof(event) === 'object' &&
        event.type === 'REQUEST' &&
        typeof(event.headers) === 'object';
}
interface IRequestV1AuthEvent extends IRequestAuthEventCommonFields {
    methodArn: string;
}
function isRequestV1(event: any): event is IRequestV1AuthEvent {
    return typeof(event) === 'object' && typeof(event.methodArn) === 'string' && isRequestAuthEvent(event);
}
interface IRequestV2AuthEvent extends IRequestAuthEventCommonFields {
    routeArn: string;
}
function isRequestV2(event: any): event is IRequestV2AuthEvent {
    return typeof(event) === 'object' && typeof(event.routeArn) === 'string' && isRequestAuthEvent(event);
}
function isAPIGatewayAuthorizerEventSubsetNeededForAuthenicateToken(event: IAPIGatewayAuthorizerEventSubsetNeededForAuthenicateToken): event is IAPIGatewayAuthorizerEventSubsetNeededForAuthenicateToken {
    return isTokenEvent(event) || isRequestV1(event) || isRequestV2(event);
}

export type IAPIGatewayAuthorizerEventSubsetNeededForAuthenicateToken = ITokenAuthEvent|IRequestV1AuthEvent|IRequestV2AuthEvent;

export interface IAuthenicateTokenOptions {
    /** The maximum number of search iterations to support when attempting to find a scope match. */
    scopeComplexityLimit?: number;
}

/**
 * 
 * @param {*} authorizerEvent 
 * @returns 
 */
// TODO: 
export async function authenticateToken(authorizerEvent: IAPIGatewayAuthorizerEventSubsetNeededForAuthenicateToken|any, audiences: string[]|any, scopes: string[]|any, options?: IAuthenicateTokenOptions|any ) {
    if (!isAPIGatewayAuthorizerEventSubsetNeededForAuthenicateToken(authorizerEvent)) { throw new Error('authorizerEvent (first param) is required and should match APIGatewayAuthorizerEvent') }
    

    if (!isStringArray(audiences)) { throw new Error('audience (second param) must be an array of strings') }
    if (!isStringArray(scopes)) { throw new Error('scopes (third param) must be an array of strings') }
    
    if (audiences.length == 0) { throw new Error('audiences (second param) cannot be an empty array') }
    if (scopes.length == 0) { throw new Error('scopes (third param) cannot be an empty array') }

    options = {
        scopeComplexityLimit: 500,
        ...(options||{})
    }
    
    const methodArn = getMethodArn(authorizerEvent);

    const token = getToken(authorizerEvent)

    const decoded = <NavexJwt>jwtdecode(token, { complete: true })
    if (!decoded?.header?.kid) {
        throw new Error('invalid token')
    }
    const { payload } = decoded
    if (!payload) {
        throw new Error('invalid token payload')
    }
    
    verifyScope(new Set(scopes), payload.scope, options.scopeComplexityLimit);

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
