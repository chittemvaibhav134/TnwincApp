const oidc = require('oidc-authorizer');

// Lambda function index.handler - thin wrapper around lib.authenticate
module.exports.handler = async (event, context) => {
  let data
  try {
    data = await oidc.authenticateToken(event, undefined, [ 'openid' ], {
      jwksUri: [ process.env.JWKS_URI, process.env.AUTH0_JWKS, process.env.ASM_JWKS ],
      methodOrRouteArn: '*'
    })
  }
  catch (err) { 
      let token = "<unavailable>"
      try {
        token = getToken(event);
      } catch {}
      console.log({ error: err, token: token});
      return context.fail(`Unauthorized`);
  }
  return data;
};

const getToken = (params) => {
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
