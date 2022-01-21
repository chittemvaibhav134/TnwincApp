const jwksBase = 'fakekeycloak.navex-dev.com';
process.env.JWKS_URI = `https://*.${jwksBase}/path/to/realm`;
import { APIGatewayAuthorizerEvent, APIGatewayRequestAuthorizerEvent } from 'aws-lambda';
import * as jwt from 'jsonwebtoken';
import { Jwt } from 'jsonwebtoken';
import { JwksClient, SigningKey } from 'jwks-rsa';


const mockGetSigningKey = jest.fn().mockImplementation((key) => {
  const signingkey = {
    publicKey: 'publicKey',
    getPublicKey: function() { return 'publicKey' }
  };
  return new Promise( (resolve, reject) => resolve(signingkey));
});
jest.mock('jwks-rsa', () => {
  return {
    JwksClient: jest.fn().mockImplementation(() => {
      return {
        getSigningKey: mockGetSigningKey,
      }
    })
  }
})
jest.mock('jsonwebtoken', () => {
  return {
    verify: jest.fn(),
    decode: jest.fn()
  }
})

import { authenticateToken } from '../index';
import { NavexJwt, NavexJwtPayload } from '../navexjwts';

function generateAuthorizerTokenEvent(): APIGatewayAuthorizerEvent {
  return {
    type: <'TOKEN'>"TOKEN",
    authorizationToken: "Bearer token",
    methodArn: "arn:to:method"
  }
}
function generateAuthorizerRequestEvent(): APIGatewayAuthorizerEvent {
  return {
    type: <'REQUEST'>'REQUEST',
    headers: {
      authorization: "Bearer faketoken"
    },
    methodArn: "arn:to:method",
    resource: 'fake-resource',
    httpMethod: 'fake-method',
    multiValueHeaders: null,
    multiValueQueryStringParameters: null,
    path: '',
    pathParameters: null,
    queryStringParameters: null,
    requestContext: null,
    stageVariables: null
  }
}
function generateJwtToken(includeClientKey: boolean) : NavexJwt {
  return {
    header: {
      kid: "fake",
      alg: 'fake-alg'
    },
    payload: <NavexJwtPayload>{
      iss: includeClientKey ? `https://clientKey.${jwksBase}/path/to/realm` : `https://${jwksBase}/path/to/realm`,
      aud: '',
      scope: '',
      session_state: "fake session",
      clientkey: includeClientKey ? "trial12" : undefined,
    },
    signature: 'fake-signature'
  }
}
function mockOnceJwtDecodeAndVerify(jwtValue: NavexJwt) {
  const jwtEncoded = JSON.stringify(jwtValue);
  (jwt.decode as jest.MockedFunction<typeof jwt.decode>).mockImplementationOnce( (token, options) => {
    return JSON.parse(jwtEncoded);
  });
  (jwt.verify as jest.MockedFunction<typeof jwt.verify>).mockImplementationOnce( (token, signingkey) => {
    return JSON.parse(jwtEncoded).payload;
  });

}

describe('Authorizer Tests', function () {
  it('Valid user token returns access policy document', async () => {
    const event = generateAuthorizerTokenEvent();
    const token = generateJwtToken(true);
    token.payload.aud = 'my-audience';
    token.payload.scope = 'fake scopes';
    mockOnceJwtDecodeAndVerify(token);

    const response = await authenticateToken(event, ['my-audience'], ['fake']);
    expect(response.policyDocument).toStrictEqual({
      Version: '2012-10-17',
      Statement: [{ Action: 'execute-api:Invoke', Effect: 'Allow', Resource: event.methodArn }]
    })
    expect(response.context).toStrictEqual({ clientkey: token.payload.clientkey, session_state: token.payload.session_state, scope: token.payload.scope })
  });


  it('Valid client credential token returns access policy document', async () => {
    const event = generateAuthorizerTokenEvent();
    const token = generateJwtToken(false);
    token.payload.aud = 'client-audience';
    token.payload.scope = 'fake scopes';
    mockOnceJwtDecodeAndVerify(token);

    const response = await authenticateToken(event, ['client-audience'], ['fake']);
    expect(response.policyDocument).toStrictEqual({
      Version: '2012-10-17',
      Statement: [{ Action: 'execute-api:Invoke', Effect: 'Allow', Resource: event.methodArn }]
    })
    expect(response.context).toStrictEqual({ clientkey: undefined, session_state: token.payload.session_state, scope: token.payload.scope })
  });


  it('valid REQUEST user token headers returns access policy', async () => {
    const event = generateAuthorizerRequestEvent();
    const token = generateJwtToken(true);
    token.payload.aud = 'request-audience';
    token.payload.scope = 'user scopes';
    mockOnceJwtDecodeAndVerify(token);

    var response = await authenticateToken(event, ['other-audience', 'websocket-audience'], ['scopes', 'that', 'overlap']);

    expect(response.policyDocument).toStrictEqual({
      Version: '2012-10-17',
      Statement: [{ Action: 'execute-api:Invoke', Effect: 'Allow', Resource: event.methodArn }]
    })
    expect(response.context).toStrictEqual({ clientkey: token.payload.clientkey, session_state: token.payload.session_state, scope: token.payload.scope })
  })
  it('valid REQUEST client creds token headers returns access policy', async () => {
    const event = generateAuthorizerRequestEvent();
    const token = generateJwtToken(false);
    token.payload.aud = 'request-audience';
    token.payload.scope = 'user scopes';
    mockOnceJwtDecodeAndVerify(token);

    var response = await authenticateToken(event, ['other-audience', 'websocket-audience'], ['scopes', 'that', 'overlap']);

    expect(response.policyDocument).toStrictEqual({
      Version: '2012-10-17',
      Statement: [{ Action: 'execute-api:Invoke', Effect: 'Allow', Resource: event.methodArn }]
    })
    expect(response.context).toStrictEqual({ clientkey: undefined, session_state: token.payload.session_state, scope: token.payload.scope })
  });


  it('valid REQUEST user token Websocket headers returns policy document', async () => {
    const event = <APIGatewayRequestAuthorizerEvent>generateAuthorizerRequestEvent();
    event.headers = {
      "Sec-WebSocket-Protocol": "bearer faketoken",
      "Connection": "upgrade",
      "Upgrade": "websocket"
    };
    const token = generateJwtToken(true);
    token.payload.aud = 'websocket-audience';
    token.payload.scope = 'web socket scopes';
    mockOnceJwtDecodeAndVerify(token);

    var response = await authenticateToken(event, ['websocket-audience'], ['scopes']);
    expect(response.policyDocument).toStrictEqual({
      Version: '2012-10-17',
      Statement: [{ Action: 'execute-api:Invoke', Effect: 'Allow', Resource: event.methodArn }]
    });
    expect(response.context).toStrictEqual({ clientkey: token.payload.clientkey, session_state: token.payload.session_state, scope: token.payload.scope });
  });

  // it('Missing ClientKey throws error', async () => {
  //   const event = {
  //     "type": "TOKEN",
  //     "authorizationToken": "Bearer token"
  //   }
  //   jwt.decode.mockImplementationOnce((token, options) => {
  //     return { header: { kid: "fake" }, payload: {} }
  //   })

  //   try {
  //     await authenticate(event)
  //   }
  //   catch (e) {
  //     expect(e.message).toMatch('token does not have clientkey')
  //   }
  // })

  // it('Missing header in token throws error', async () => {
  //   const event = {
  //     "type": "TOKEN",
  //     "authorizationToken": "Bearer token"
  //   }
  //   jwt.decode.mockImplementationOnce((token, options) => {
  //     return { payload: { clientkey: "fake" } }
  //   })
  //   try {
  //     await authenticate(event)
  //   }
  //   catch (e) {
  //     expect(e.message).toMatch('invalid token')
  //   }
  // })

  // it('Missing kid in token throws error', async () => {
  //   const event = {
  //     "type": "TOKEN",
  //     "authorizationToken": "Bearer token"
  //   }
  //   jwt.decode.mockImplementationOnce((token, options) => {
  //     return { header: { notkid: "fake" }, payload: {} }
  //   })

  //   try {
  //     await authenticate(event)
  //   }
  //   catch (e) {
  //     expect(e.message).toMatch('invalid token')
  //   }
  // })

  // it('Missing Event Type throws error', async () => {
  //   const event = {
  //     "authorizationToken": "Bearer token"
  //   }

  //   try {
  //     await authenticate(event)
  //   }
  //   catch (e) {
  //     expect(e.message).toMatch('Expected "event.type" parameter to have value "TOKEN" or "REQUEST"')
  //   }
  // })

  // it('Invalid Event Type throws error', async () => {
  //   const event = {
  //     "type": "invalidEvent",
  //     "authorizationToken": "Bearer token"
  //   }

  //   try {
  //     await authenticate(event)
  //   }
  //   catch (e) {
  //     expect(e.message).toMatch('Expected "event.type" parameter to have value "TOKEN" or "REQUEST"')
  //   }
  // })

  // it('Token request with missing header throws error', async () => {
  //   const event = {
  //     "type": "TOKEN"
  //   }

  //   try {
  //     await authenticate(event)
  //   }
  //   catch (e) {
  //     expect(e.message).toMatch('Expected "event.headers.Authorization" parameter to be set')
  //   }
  // })

  // it('invalid format of Token request throws error', async () => {
  //   const event = {
  //     "type": "TOKEN",
  //     "authorizationToken": "invalid format"
  //   }

  //   try {
  //     await authenticate(event)
  //   }
  //   catch (e) {
  //     expect(e.message).toMatch('Invalid Authorization token - invalid format does not match \"Bearer .*\"')
  //   }
  // })

  // it('Request event missing headers throws error', async () => {
  //   const event = {
  //     "type": "REQUEST"
  //   }
  //   try {
  //     await authenticate(event)
  //   }
  //   catch (e) {
  //     expect(e.message).toMatch('Expected \"event.headers\" parameter to be set')
  //   }
  // })

  // it('invalid sub protocol for websocket request throws error', async () => {
  //   const event = {
  //     "type": "REQUEST",
  //     "headers": {
  //       "Sec-WebSocket-Protocol": "invalid protocol",
  //       "Connection": "upgrade",
  //       "Upgrade": "websocket"
  //     }
  //   }

  //   try {
  //     await authenticate(event)
  //   }
  //   catch (e) {
  //     expect(e.message).toMatch('Invalid sub protocol.')
  //   }
  // })
})
