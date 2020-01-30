require('dotenv').config({ silent: true });
const https = require('https')
const url = require('url')
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
const getToken = async (params) => {
    if (!params.type || params.type !== 'REQUEST') {
        throw new Error('Expected "event.type" parameter to have value "REQUEST"');
    }

    const tokenString = params.headers.Authorization;
    if (!tokenString) {
        throw new Error('Expected "event.headers.Authorization" parameter to be set');
    }

    const match = tokenString.match(/^Bearer (.*)$/);
    if (!match || match.length < 2) {
        throw new Error(`Invalid Authorization token - ${tokenString} does not match "Bearer .*"`);
    }
    return match[1];
}

const getClientKey = async (refererUrl) => {
    const parsedUrl = new url.URL(refererUrl)
    if (parsedUrl.host.startsWith('navexadmin')) {
        return 'navex'
    } else {
        return parsedUrl.pathname.split('/')[1]
    }
}

const getKeyCloakUrl = async (params) => {
    var clientkey = await getClientKey(params.headers.Referer)
    var keycloakUrl = `${process.env.USER_INFO_URI}`
    keycloakUrl = keycloakUrl.replace('*', clientkey)
    return new url.URL(keycloakUrl)
}

module.exports.authenticate = async (params) => {
    const token = await getToken(params);

    const decoded = jwt.decode(token, { complete: true });
    if (!decoded || !decoded.header || !decoded.header.kid) {
        throw new Error('invalid token');
    }

    var clientkey = await getClientKey(params.headers.Referer)

    const client = jwksClient({
        cache: true,
        rateLimit: true,
        jwksRequestsPerMinute: 10, // Default value
        jwksUri: process.env.JWKS_URI.replace('*', clientkey),
        strictSsl: false
    });

    const getSigningKey = util.promisify(client.getSigningKey);
    return getSigningKey(decoded.header.kid)
        .then((key) => {
            const signingKey = key.publicKey || key.rsaPublicKey;
            return jwt.verify(token, signingKey);
        })
        .then((decoded)=> ({
            principalId: decoded.sub,
            policyDocument: getPolicyDocument('Allow', params.methodArn),
            context: { scope: decoded.scope }
        }));
}

module.exports.authorize = async (params) => {
    var keycloakResponse = await getUserRole(params)
    if (keycloakResponse.statusCode === 401) {
        throw new Error(`${keycloakResponse.data.error} ${keycloakResponse.data.error_description}`)
    } else if (keycloakResponse.data.user_store_role !== 'UserStoreAdministrator' &&
        keycloakResponse.data.user_store_role !== 'NavexAdministrator') {
        throw new Error('Unauthorized role for this endpoint');
    } else if (keycloakResponse.statusCode !== 200) {
        throw new Error('Failed to authorize user')
    }
}

const getUserRole = async (params) => {
    const token = await getToken(params)
    var parsedUrl = await getKeyCloakUrl(params)
    const options = {
        method: 'GET',
        host: parsedUrl.host,
        path: parsedUrl.pathname,
        headers: {
            Authorization: `Bearer ${token}`
        }
    }
    if (process.env.LOCAL) {
        options.headers = {
            ...options.headers,
            Host: options.host
        }
        options.port = '8443'
        options.host = 'trial12.keycloak.devlocal.navex-pe.com'

        options.rejectUnauthorized = false
    }
    return new Promise((resolve, reject) => {
        const req = https.request(options, (res) => {
            const { statusCode, statusMessage, headers } = res

            let data = ''
            res.setEncoding('utf-8')
            res.on('data', (chunk) => { data += chunk })
            res.on('end', () => {
                resolve({
                    data: JSON.parse(data),
                    statusCode,
                    statusMessage,
                    headers
                })
            })
        })
        req.on('error', (err) => {
            console.error('Error validating token', err)
            reject(err)
        })
        req.end(options.body)
    })
}
