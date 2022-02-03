// Order matters (tests-common has mocking side effects)
import { generateAuthorizerRequestEvent, generateAuthorizerTokenEvent, generateJwtToken, mockOnceJwtDecodeAndVerify } from "./tests-common";
import { authenticateToken } from "..";

describe('Authorizer Invalid calls to authenicateToken', function () {
    it('Missing Event throws error', async () => {
        await expect(authenticateToken(undefined, ['my-audience'], ['two-scope']))
            .rejects.toThrowError('authorizerEvent is required and should match APIGatewayAuthorizerEvent')
    });
    it('Missing Event Type throws error', async () => {
        const event = generateAuthorizerTokenEvent();
        delete event.type;

        await expect(authenticateToken(event, ['no-audience'], ['no-scope']))
            .rejects.toThrowError('Expected "event.type" parameter to have value "TOKEN" or "REQUEST"')
    })

    it('Invalid Event Type throws error', async () => {
        const event = generateAuthorizerTokenEvent();
        const altEvent = <any>event; // use casted reference to get around type checking
        altEvent.type = 'invalidEvent';

        await expect(authenticateToken(event, ['no-audience'], ['no-scope']))
            .rejects.toThrowError('Expected "event.type" parameter to have value "TOKEN" or "REQUEST"')
    })

    it('Token request with missing authorizationToken throws error', async () => {
        const event = generateAuthorizerTokenEvent();
        delete event.authorizationToken;

        await expect(authenticateToken(event, ['no-audience'], ['no-scope']))
            .rejects.toThrowError('Expected "event.authorizationToken" parameter to be set')
    });

    it('Token request with missing methodArn throws error', async () => {
        const event = generateAuthorizerTokenEvent();
        delete event.methodArn;

        await expect(authenticateToken(event, ['no-audience'], ['no-scope']))
            .rejects.toThrowError('authorizerEvent.methodArn must be set')
    });

    it('invalid format of Token request throws error', async () => {
        const event = generateAuthorizerTokenEvent();
        event.authorizationToken = 'invalid format';

        await expect(authenticateToken(event, ['no-audience'], ['no-scope']))
            .rejects.toThrowError('Invalid Authorization token - invalid format does not match "Bearer .*"')
    });

    it('Request event missing headers throws error', async () => {
        const event = generateAuthorizerRequestEvent();
        delete event.headers;

        await expect(authenticateToken(event, ['no-audience'], ['no-scope']))
            .rejects.toThrowError('Expected "event.headers" parameter to be set');
    })

    it('invalid sub protocol for websocket request throws error', async () => {
      const event = generateAuthorizerRequestEvent();
      event.headers = {
        "Sec-WebSocket-Protocol": "invalid protocol",
        "Connection": "upgrade",
        "Upgrade": "websocket"
      };

        await expect(authenticateToken(event, ['no-audience'], ['no-scope']))
            .rejects.toThrowError('Invalid sub protocol.')
    });

    it('Empty audience array throw error', async () => {
        const event = generateAuthorizerTokenEvent();
        await expect(authenticateToken(event, [], ['no-scope']))
            .rejects.toThrowError('audiences cannot be an empty array')
    });

    it('Missing audience throws error', async () => {
        const event = generateAuthorizerTokenEvent();
        await expect(authenticateToken(event, null, ['no-scope']))
            .rejects.toThrowError('audience is required and must be an array')
    });

    it('Empty scope array throw error', async () => {
        const event = generateAuthorizerTokenEvent();
        await expect(authenticateToken(event, ['no-audience'], []))
            .rejects.toThrowError('scopes cannot be an empty array')
    });

    it('Missing scope throws error', async () => {
        const event = generateAuthorizerTokenEvent();
        await expect(authenticateToken(event, ['no-audience'], undefined))
            .rejects.toThrowError('scopes is required and must be an array');
    });

})