// Order matters (tests-common has mocking side effects)
import { generateAuthorizerRequestEvent, generateAuthorizerTokenEvent, generateJwtToken, mockOnceJwtDecodeAndVerify } from "./tests-common";
import { authenticateToken } from "..";

describe('Authorizer Invalid calls to authenicateToken', function () {
    it('Missing Event throws error', async () => {
        try {
            await authenticateToken(undefined, ['my-audience'], ['two-scope']);
        }
        catch (e) {
            expect(e.message).toMatch('authorizerEvent is required and should match APIGatewayAuthorizerEvent')
        }
    });
    it('Missing Event Type throws error', async () => {
        const event = generateAuthorizerTokenEvent();
        delete event.type;

        try {
            await authenticateToken(event, ['no-audience'], ['no-scope'])
        }
        catch (e) {
            expect(e.message).toMatch('Expected "event.type" parameter to have value "TOKEN" or "REQUEST"')
        }
    })

    it('Invalid Event Type throws error', async () => {
        const event = generateAuthorizerTokenEvent();
        const altEvent = <any>event; // use casted reference to get around type checking
        altEvent.type = 'invalidEvent';

        try {
            await authenticateToken(event, ['no-audience'], ['no-scope'])
        }
        catch (e) {
            expect(e.message).toMatch('Expected "event.type" parameter to have value "TOKEN" or "REQUEST"')
        }
    })

    it('Token request with missing authorizationToken throws error', async () => {
        const event = generateAuthorizerTokenEvent();
        delete event.authorizationToken;

        try {
            await authenticateToken(event, ['no-audience'], ['no-scope'])
        }
        catch (e) {
            expect(e.message).toMatch('Expected "event.authorizationToken" parameter to be set')
        }
    });

    it('Token request with missing methodArn throws error', async () => {
        const event = generateAuthorizerTokenEvent();
        delete event.methodArn;

        try {
            await authenticateToken(event, ['no-audience'], ['no-scope'])
        }
        catch (e) {
            expect(e.message).toMatch('authorizerEvent.methodArn must be set')
        }
    });

    it('invalid format of Token request throws error', async () => {
        const event = generateAuthorizerTokenEvent();
        event.authorizationToken = 'invalid format';

        try {
            await authenticateToken(event, ['no-audience'], ['no-scope'])
        }
        catch (e) {
            expect(e.message).toMatch('Invalid Authorization token - invalid format does not match "Bearer .*"')
        }
    });

    it('Request event missing headers throws error', async () => {
        const event = generateAuthorizerRequestEvent();
        delete event.headers;

        try {
            await authenticateToken(event, ['no-audience'], ['no-scope']);
        }
        catch (e) {
            expect(e.message).toMatch('Expected "event.headers" parameter to be set');
        }
    })

    it('invalid sub protocol for websocket request throws error', async () => {
      const event = generateAuthorizerRequestEvent();
      event.headers = {
        "Sec-WebSocket-Protocol": "invalid protocol",
        "Connection": "upgrade",
        "Upgrade": "websocket"
      };

      try {
        await authenticateToken(event, ['no-audience'], ['no-scope'])
      }
      catch (e) {
        expect(e.message).toMatch('Invalid sub protocol.')
      }
    });

    it('Empty audience array throw error', async () => {
        const event = generateAuthorizerTokenEvent();
        try {
            await authenticateToken(event, [], ['no-scope'])
        }
        catch (e) {
            expect(e.message).toMatch('audiences cannot be an empty array')
        }
    });

    it('Missing audience throws error', async () => {
        const event = generateAuthorizerTokenEvent();
        try {
            await authenticateToken(event, null, ['no-scope'])
        }
        catch (e) {
            expect(e.message).toMatch('audience is required and must be an array')
        }
    });

    it('Empty scope array throw error', async () => {
        const event = generateAuthorizerTokenEvent();
        try {
            await authenticateToken(event, ['no-audience'], [])
        }
        catch (e) {
            expect(e.message).toMatch('scopes cannot be an empty array')
        }
    });

    it('Missing scope throws error', async () => {
        const event = generateAuthorizerTokenEvent();
        try {
            await authenticateToken(event, ['no-audience'], undefined)
        }
        catch (e) {
            expect(e.message).toMatch('scopes is required and must be an array')
        }
    });

})