const jwksBase = 'fakekeycloak.navex-dev.com';
process.env.JWKS_URI = `https://*.${jwksBase}/path/to/realm`;
import { APIGatewayRequestAuthorizerEvent, APIGatewayTokenAuthorizerEvent } from 'aws-lambda';
import * as jwt from 'jsonwebtoken';

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

import { NavexJwt, NavexJwtPayload } from '../navexjwts';

export function generateAuthorizerTokenEvent(): APIGatewayTokenAuthorizerEvent {
  return {
    type: "TOKEN" as const,
    authorizationToken: "Bearer token",
    methodArn: "arn:to:method"
  }
}
export function generateAuthorizerRequestEvent(): APIGatewayRequestAuthorizerEvent {
  return {
    type: 'REQUEST' as const,
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
export function generateJwtToken(clientKey: string) : NavexJwt {
  const hasClientKey = clientKey && clientKey.length > 0;
  const jwt = {
    header: {
      kid: "fake",
      alg: 'fake-alg'
    },
    payload: <NavexJwtPayload>{
      iss: hasClientKey ? `https://${clientKey}.${jwksBase}/path/to/realm` : `https://${jwksBase}/path/to/realm`,
      aud: 'fake-audience',
      scope: '',
      session_state: "fake session"
    },
    signature: 'fake-signature'
  }
  if (hasClientKey) {
    jwt.payload.clientkey = clientKey;
  }
  return jwt;
}
export function mockOnceJwtDecodeAndVerify(jwtValue: NavexJwt) {
  const jwtEncoded = JSON.stringify(jwtValue);
  (jwt.decode as jest.MockedFunction<typeof jwt.decode>).mockImplementationOnce( (token, options) => {
    return JSON.parse(jwtEncoded);
  });
  (jwt.verify as jest.MockedFunction<typeof jwt.verify>).mockImplementationOnce( (token, signingkey) => {
    return JSON.parse(jwtEncoded).payload;
  });

}