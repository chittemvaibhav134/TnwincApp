import { JwksClient } from 'jwks-rsa';
import { decode as jwtdecode, verify as jwtverify } from 'jsonwebtoken';
import { APIGatewayAuthorizerEvent, APIGatewayRequestAuthorizerEvent, APIGatewayRequestAuthorizerEventV2, PolicyDocument } from 'aws-lambda';
import { isStringArray } from './util';
import { verifyScope } from './scope';
import { NavexJwt, NavexJwtPayload } from './navexjwts';

/** Creates an IAM PolicyDocument from the given parameters. */
const getPolicyDocument = (effect: string, resource: string|string[]): PolicyDocument => {
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

function buildJwksUriFromIssuer(token: NavexJwt, options: IAuthenicateTokenOptions): string {
    if (!token.payload.iss) { throw new Error('invalid issuer') }
    const jwksUriSet = Array.isArray(options.jwksUri) ? options.jwksUri : [options.jwksUri];
    const issuerHostname = new URL(token.payload.iss).hostname
    for(const jwksTemplate of jwksUriSet) {
        const jwksHostname = new URL(jwksTemplate).hostname
        const jwksIsTemplate = jwksHostname.startsWith('*.');
        const jwksHostnamePlain = jwksIsTemplate ? jwksHostname.substring('*.'.length) : jwksHostname;
        if(issuerHostname.endsWith(jwksHostnamePlain)) {
            if( jwksIsTemplate ) {
                const clientKey = getClientKey(token);
                return jwksTemplate.replace('*', clientKey)
            } else {
                return jwksTemplate.replace('*.', '');
            }
        }
    }
    throw new Error(`Could not find matching JWKS base for issuer host ${issuerHostname}`);
}

const jwksClients = new Map<string, JwksClient>();
function getJwksClient(token: NavexJwt, options: IAuthenicateTokenOptions): JwksClient {
    const jwksUri = buildJwksUriFromIssuer(token, options);
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
    jwksUri: string|string[];
    methodOrRouteArn?: string|string[];
}
function isAuthenicateTokenOptions(options: any): options is IAuthenicateTokenOptions {
    return typeof(options) === 'object' &&
        ['undefined', 'number'].includes(typeof(options.scopeComplexityLimit)) &&
        (typeof(options.jwksUri) === 'string' ||
        isStringArray(options.jwksUri)) &&
        (['undefined', 'string'].includes(typeof(options.methodOrRouteArn)) || 
            (Array.isArray(options.methodOrRouteArn) && options.methodOrRouteArn.length > 0 && typeof(options.methodOrRouteArn[0]) === 'string'));
}

/**
 * 
 * @param {*} authorizerEvent 
 * @returns 
 */
// TODO: 
export async function authenticateToken(authorizerEvent: IAPIGatewayAuthorizerEventSubsetNeededForAuthenicateToken, audiences: string[]|undefined , scopes: string[], options: IAuthenicateTokenOptions ) {
    if (!isAPIGatewayAuthorizerEventSubsetNeededForAuthenicateToken(authorizerEvent)) { throw new Error('authorizerEvent (first param) is required and should match APIGatewayAuthorizerEvent') }
    

    if (audiences !== undefined && !isStringArray(audiences)) { throw new Error('audience (second param) must be an array of strings or omitted') }
    if (!isStringArray(scopes)) { throw new Error('scopes (third param) must be an array of strings') }
    
    if (audiences !== undefined && audiences.length == 0) { throw new Error('audiences (second param) cannot be an empty array unless omitted') }

    if (scopes.length == 0) { throw new Error('scopes (third param) cannot be an empty array') }

    if (!isAuthenicateTokenOptions(options)) { throw new Error('options (fourth param) is required and must match IAuthenicateTokenOptions') }

    // Provide default for scopeComplexityLimit
    options = {
        scopeComplexityLimit: 500,
        methodOrRouteArn: getMethodArn(authorizerEvent),
        ...options
    };
    
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

    const client = getJwksClient(decoded, options);

    const key = await client.getSigningKey(decoded.header.kid);
    const signingKey = key.getPublicKey();
    const verifiedPayload = <NavexJwtPayload>jwtverify(token, signingKey, { audience: audiences });
    return ({
        principalId: verifiedPayload.sub,
        policyDocument: getPolicyDocument('Allow', options.methodOrRouteArn),
        context: { scope: verifiedPayload.scope, session_state: verifiedPayload.session_state, clientkey: verifiedPayload.clientkey }
    });
}
