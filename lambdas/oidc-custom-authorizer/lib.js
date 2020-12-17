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
        throw new Error('Expected "event.type" parameter to have value "TOKEN"');
    }

    const eventType = params.type;

    if (eventType === 'TOKEN') {
        const tokenString = params.authorizationToken;
        if (!tokenString) {
            throw new Error('Expected "event.headers.Authorization" parameter to be set');
        }

        const match = tokenString.match(/^Bearer (.*)$/);
        if (!match || match.length < 2) {
            throw new Error(`Invalid Authorization token - ${tokenString} does not match "Bearer .*"`);
        }
        return match[1];
    } else if (eventType === 'REQUEST') {
        return getWebSocketRequestToken(params);
    } else {
        throw new Error('Expected "event.type" parameter to have value "TOKEN"');
    }
}

const getWebSocketRequestToken = (request) => {
    const headers = request.headers;
    if (!headers) {
        throw new Error('Expected "event.headers" parameter to be set');
    }

    if (headers.Connection === "upgrade" && headers.Upgrade === "websocket") {
        let token = null;
        subProtocolIsValid(headers['Sec-WebSocket-Protocol'], 
            tokenString => token = tokenString, 
            () => { throw new Error('Invalid sub protocol.'); }
        );
        return token?.trim();
    } else {
        throw new Error('Invalid WebSocket request because not all required headers are present: connection, upgrade, sec-websocket-protocol.');
    }
}

const subProtocolIsValid = (subProtocolHeader, setTokenString, onerror) => {
    const subProtocols = subProtocolHeader.split(',')
    if (subProtocols.indexOf('bearer') >= 0) {
        setTokenString(subProtocols[1]);
    } else {
        onerror();
    }
}

const getClientKey = (decodedToken) => {
    if(!decodedToken.payload || !decodedToken.payload.clientkey) {
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
        .then((decoded)=> ({
            principalId: decoded.sub,
            policyDocument: getPolicyDocument('Allow','*'),
            context: { scope: decoded.scope }
        }));
}
