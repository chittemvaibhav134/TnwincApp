process.env.JWKS_URI = "https://*.fakekeycloak.navex-dev.com"
const jwt = require('jsonwebtoken');

const mockGetSigningKey = jest.fn().mockImplementation((key, callback) => {
  const signingkey = { publicKey: 'publicKey' };
  callback(null, signingkey);
});
jest.mock('jwks-rsa', () => {
  return jest.fn().mockImplementation(() => {
    return { getSigningKey: mockGetSigningKey }
  })
})
jest.mock('jsonwebtoken', () => {
  return {
    verify: jest.fn(),
    decode: jest.fn()
  }
})

const { authenticate } = require('../lib');

describe('Authorizer Tests', function () {
  it('Valid token returns access policy document', async () => {
    const event = {
      "type": "TOKEN",
      "authorizationToken": "Bearer token"
    }
    jwt.decode.mockImplementationOnce((token, options) => {
      return { session_state: "fake session", scope: "fake scope", header: { kid: "fake" }, payload: { clientkey: "trial12" } }
    })
    jwt.verify.mockImplementationOnce((token, signingkey) => {
      return { session_state: "fake session", scope: "fake scope", header: { kid: "fake" }, payload: { clientkey: "trial12" } }
    })
    var response = await authenticate(event)
    expect(response.policyDocument).toStrictEqual({
      Version: '2012-10-17',
      Statement: [{ Action: 'execute-api:Invoke', Effect: 'Allow', Resource: '*' }]
    })
    expect(response.context).toStrictEqual({ clientkey: 'trial12', session_state: 'fake session', scope: 'fake scope' })
  });

  it('valid REQUEST headers returns access policy', async () => {
    const event = {
      "type": "REQUEST",
      "headers": { "authorization": "Bearer faketoken" }
    }
    jwt.decode.mockImplementationOnce((token, options) => {
      return { session_state: "fake session", scope: "fake scope", header: { kid: "fake" }, payload: { clientkey: "trial12" } }
    })
    jwt.verify.mockImplementationOnce((token, signingkey) => {
      return { session_state: "fake session", scope: "fake scope", header: { kid: "fake" }, payload: { clientkey: "trial12" } }
    })
    var response = await authenticate(event)
    expect(response.policyDocument).toStrictEqual({
      Version: '2012-10-17',
      Statement: [{ Action: 'execute-api:Invoke', Effect: 'Allow', Resource: '*' }]
    })
    expect(response.context).toStrictEqual({ clientkey: 'trial12', session_state: 'fake session', scope: 'fake scope' })
  })

  it('valid REQUEST Websocket headers returns policy document', async () => {
    const event = {
      "type": "REQUEST",
      "headers": {
        "Sec-WebSocket-Protocol": "bearer faketoken",
        "Connection": "upgrade",
        "Upgrade": "websocket"
      }
    }
    jwt.decode.mockImplementationOnce((token, options) => {
      return { session_state: "fake session", scope: "fake scope", header: { kid: "fake" }, payload: { clientkey: "trial12" } }
    })
    jwt.verify.mockImplementationOnce((token, signingkey) => {
      return { session_state: "fake session", scope: "fake scope", header: { kid: "fake" }, payload: { clientkey: "trial12" } }
    })
    var response = await authenticate(event)
    expect(response.policyDocument).toStrictEqual({
      Version: '2012-10-17',
      Statement: [{ Action: 'execute-api:Invoke', Effect: 'Allow', Resource: '*' }]
    })
    expect(response.context).toStrictEqual({ clientkey: 'trial12', session_state: 'fake session', scope: 'fake scope' })
  })

  it('Missing ClientKey throws error', async () => {
    const event = {
      "type": "TOKEN",
      "authorizationToken": "Bearer token"
    }
    jwt.decode.mockImplementationOnce((token, options) => {
      return { header: { kid: "fake" }, payload: {} }
    })

    try {
      await authenticate(event)
    }
    catch (e) {
      expect(e.message).toMatch('token does not have clientkey')
    }
  })

  it('Missing header in token throws error', async () => {
    const event = {
      "type": "TOKEN",
      "authorizationToken": "Bearer token"
    }
    jwt.decode.mockImplementationOnce((token, options) => {
      return { payload: { clientkey: "fake" } }
    })
    try {
      await authenticate(event)
    }
    catch (e) {
      expect(e.message).toMatch('invalid token')
    }
  })

  it('Missing kid in token throws error', async () => {
    const event = {
      "type": "TOKEN",
      "authorizationToken": "Bearer token"
    }
    jwt.decode.mockImplementationOnce((token, options) => {
      return { header: { notkid: "fake" }, payload: {} }
    })

    try {
      await authenticate(event)
    }
    catch (e) {
      expect(e.message).toMatch('invalid token')
    }
  })

  it('Missing Event Type throws error', async () => {
    const event = {
      "authorizationToken": "Bearer token"
    }

    try {
      await authenticate(event)
    }
    catch (e) {
      expect(e.message).toMatch('Expected "event.type" parameter to have value "TOKEN" or "REQUEST"')
    }
  })

  it('Invalid Event Type throws error', async () => {
    const event = {
      "type": "invalidEvent",
      "authorizationToken": "Bearer token"
    }

    try {
      await authenticate(event)
    }
    catch (e) {
      expect(e.message).toMatch('Expected "event.type" parameter to have value "TOKEN" or "REQUEST"')
    }
  })

  it('Token request with missing header throws error', async () => {
    const event = {
      "type": "TOKEN"
    }

    try {
      await authenticate(event)
    }
    catch (e) {
      expect(e.message).toMatch('Expected "event.headers.Authorization" parameter to be set')
    }
  })

  it('invalid format of Token request throws error', async () => {
    const event = {
      "type": "TOKEN",
      "authorizationToken": "invalid format"
    }

    try {
      await authenticate(event)
    }
    catch (e) {
      expect(e.message).toMatch('Invalid Authorization token - invalid format does not match \"Bearer .*\"')
    }
  })

  it('Request event missing headers throws error', async () => {
    const event = {
      "type": "REQUEST"
    }
    try {
      await authenticate(event)
    }
    catch (e) {
      expect(e.message).toMatch('Expected \"event.headers\" parameter to be set')
    }
  })

  it('invalid sub protocol for websocket request throws error', async () => {
    const event = {
      "type": "REQUEST",
      "headers": {
        "Sec-WebSocket-Protocol": "invalid protocol",
        "Connection": "upgrade",
        "Upgrade": "websocket"
      }
    }

    try {
      await authenticate(event)
    }
    catch (e) {
      expect(e.message).toMatch('Invalid sub protocol.')
    }
  })
})
