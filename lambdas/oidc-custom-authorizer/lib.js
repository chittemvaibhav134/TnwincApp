require('dotenv').config({ silent: true });
const jwksClient = require('jwks-rsa');
const jwt = require('jsonwebtoken');
const util = require('util');

const getPolicyDocument = (effect, resource) => {
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


// extract and return the Bearer Token from the Lambda event parameters
const getToken = (params) => {
    if (!params.type) {
        throw new Error('Expected "event.type" parameter to have value "TOKEN" or "REQUEST"');
    }

    const eventType = params.type;

    if (eventType === 'TOKEN') {
        const tokenString = params.authorizationToken;
        if (!tokenString) {
            throw new Error('Expected "event.headers.Authorization" parameter to be set');
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

const getRequestToken = (tokenString) => {
    const match = tokenString.match(/^Bearer (.*)$/);
    if (!match || match.length < 2) {
        throw new Error(`Invalid Authorization token - ${tokenString} does not match "Bearer .*"`);
    }
    return match[1];
}

const getWebSocketRequestToken = (request) => {
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

const getClientKey = (decodedToken) => {
    if (!decodedToken.payload || !decodedToken.payload.clientkey) {
        throw new Error('token does not have clientkey')
    }
    return decodedToken.payload.clientkey
}

module.exports.authenticate = (params) => {
    const token = getToken(params);

    const decoded = jwt.decode(token, { complete: true });
    if (!decoded || !decoded.header || !decoded.header.kid) {
        throw new Error('invalid token');
    }

    var clientkey = getClientKey(decoded)

    const client = jwksClient({
        cache: true,
        rateLimit: true,
        jwksRequestsPerMinute: 10, // Default value
        jwksUri: process.env.JWKS_URI.replace('*', clientkey),
    });

    const getSigningKey = util.promisify(client.getSigningKey);
    return getSigningKey(decoded.header.kid)
        .then((key) => {
            const signingKey = key.publicKey || key.rsaPublicKey;
            return jwt.verify(token, signingKey);
        })
        .then((decoded) => ({
            principalId: decoded.sub,
            policyDocument: getPolicyDocument('Allow', '*'),
            context: { scope: decoded.scope, session_state: decoded.session_state, clientkey: clientkey }
        }));
}
