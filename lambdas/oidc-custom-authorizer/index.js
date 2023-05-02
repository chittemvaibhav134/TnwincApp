const oidc = require('oidc-authorizer');

// Lambda function index.handler - thin wrapper around lib.authenticate
module.exports.handler = async (event, context) => {
  let data
  try {
    data = await oidc.authenticateToken(event, undefined, [ 'openid' ], {
      jwksUri: [ process.env.JWKS_URI, process.env.AUTH0_JWKS ],
      methodOrRouteArn: '*'
    })
  }
  catch (err) { 
      let token = "<unavailable>"
      try {
        token = lib.getToken(event);
      } catch {}
      console.log({ error: err, token: token});
      return context.fail(`Unauthorized`);
  }
  return data;
};
