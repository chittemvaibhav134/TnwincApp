// Order matters (tests-common has mocking side effects)
import { generateAuthorizerTokenEvent, generateJwtToken, mockOnceJwtDecodeAndVerify, generateAuthorizerRequestEvent, callDefaultOptions } from "./tests-common";
import { authenticateToken } from "..";

describe('Authorizer Valid State Tests', function () {
    it('Valid user token returns access policy document', async () => {
        const event = generateAuthorizerTokenEvent();
        const token = generateJwtToken('trial12');
        token.payload.scope = 'fake scopes';
        mockOnceJwtDecodeAndVerify(token);
    
        const response = await authenticateToken(event, ['my-audience'], ['fake'], callDefaultOptions);
        expect(response.policyDocument).toStrictEqual({
          Version: '2012-10-17',
          Statement: [{ Action: 'execute-api:Invoke', Effect: 'Allow', Resource: event.methodArn }]
        })
        expect(response.context).toStrictEqual({ clientkey: token.payload.clientkey, session_state: token.payload.session_state, scope: token.payload.scope })
      });
    
    
      it('Valid client creds token returns access policy document', async () => {
        const event = generateAuthorizerTokenEvent();
        const token = generateJwtToken(undefined);
        token.payload.scope = 'fake scopes';
        mockOnceJwtDecodeAndVerify(token);
    
        const response = await authenticateToken(event, ['client-audience'], ['fake'], callDefaultOptions);
        expect(response.policyDocument).toStrictEqual({
          Version: '2012-10-17',
          Statement: [{ Action: 'execute-api:Invoke', Effect: 'Allow', Resource: event.methodArn }]
        })
        expect(response.context).toStrictEqual({ clientkey: undefined, session_state: token.payload.session_state, scope: token.payload.scope })
      });
    
    
      it('valid REQUEST user token headers returns access policy', async () => {
        const event = generateAuthorizerRequestEvent();
        const token = generateJwtToken('trial12');
        token.payload.scope = 'user scopes';
        mockOnceJwtDecodeAndVerify(token);
    
        var response = await authenticateToken(event, ['websocket-audience'], ['scopes', 'that', 'overlap'], callDefaultOptions);
    
        expect(response.policyDocument).toStrictEqual({
          Version: '2012-10-17',
          Statement: [{ Action: 'execute-api:Invoke', Effect: 'Allow', Resource: event.methodArn }]
        })
        expect(response.context).toStrictEqual({ clientkey: token.payload.clientkey, session_state: token.payload.session_state, scope: token.payload.scope })
      })

      it('valid REQUEST V2 user token headers returns access policy', async () => {
        const event = generateAuthorizerRequestEvent();
        const altEvent = (<any>event);
        altEvent.version = "2.0";
        altEvent.routeArn = event.methodArn;
        delete altEvent.methodArn;

        const token = generateJwtToken('trial12');
        token.payload.scope = 'user scopes';
        mockOnceJwtDecodeAndVerify(token);
    
        var response = await authenticateToken(event, ['websocket-audience'], ['scopes', 'that', 'overlap'], callDefaultOptions);
    
        expect(response.policyDocument).toStrictEqual({
          Version: '2012-10-17',
          Statement: [{ Action: 'execute-api:Invoke', Effect: 'Allow', Resource: altEvent.routeArn }]
        })
        expect(response.context).toStrictEqual({ clientkey: token.payload.clientkey, session_state: token.payload.session_state, scope: token.payload.scope })
      })

      it('valid REQUEST client creds token headers returns access policy', async () => {
        const event = generateAuthorizerRequestEvent();
        const token = generateJwtToken(undefined);
        token.payload.scope = 'user scopes';
        mockOnceJwtDecodeAndVerify(token);
    
        var response = await authenticateToken(event, ['other-audience', 'websocket-audience'], ['scopes', 'that', 'overlap'], callDefaultOptions);
    
        expect(response.policyDocument).toStrictEqual({
          Version: '2012-10-17',
          Statement: [{ Action: 'execute-api:Invoke', Effect: 'Allow', Resource: event.methodArn }]
        })
        expect(response.context).toStrictEqual({ clientkey: undefined, session_state: token.payload.session_state, scope: token.payload.scope })
      });
    
    
      it('valid REQUEST user token Websocket headers returns policy document', async () => {
        const event = generateAuthorizerRequestEvent();
        event.headers = {
          "Sec-WebSocket-Protocol": "bearer faketoken",
          "Connection": "upgrade",
          "Upgrade": "websocket"
        };
        const token = generateJwtToken('trial12');
        token.payload.scope = 'web socket scopes';
        mockOnceJwtDecodeAndVerify(token);
    
        var response = await authenticateToken(event, ['websocket-audience'], ['scopes'], callDefaultOptions);
        expect(response.policyDocument).toStrictEqual({
          Version: '2012-10-17',
          Statement: [{ Action: 'execute-api:Invoke', Effect: 'Allow', Resource: event.methodArn }]
        });
        expect(response.context).toStrictEqual({ clientkey: token.payload.clientkey, session_state: token.payload.session_state, scope: token.payload.scope });
      });
      it('valid REQUEST client creds Websocket headers returns policy document', async () => {
        const event = generateAuthorizerRequestEvent();
        event.headers = {
          "Sec-WebSocket-Protocol": "bearer faketoken",
          "Connection": "upgrade",
          "Upgrade": "websocket"
        };
        const token = generateJwtToken(undefined);
        token.payload.scope = 'web socket scopes';
        mockOnceJwtDecodeAndVerify(token);
    
        var response = await authenticateToken(event, ['websocket-audience-cc'], ['scopes'], callDefaultOptions);
        expect(response.policyDocument).toStrictEqual({
          Version: '2012-10-17',
          Statement: [{ Action: 'execute-api:Invoke', Effect: 'Allow', Resource: event.methodArn }]
        });
        expect(response.context).toStrictEqual({ clientkey: undefined, session_state: token.payload.session_state, scope: token.payload.scope });
      });
});