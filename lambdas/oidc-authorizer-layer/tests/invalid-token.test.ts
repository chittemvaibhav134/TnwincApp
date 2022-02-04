// Order matters (tests-common has mocking side effects)
import { callDefaultOptions, generateAuthorizerTokenEvent, generateJwtToken, mockOnceJwtDecodeAndVerify } from "./tests-common";
import { authenticateToken } from "..";

// The TOKEN event type is used throughout this section, it is assumed that
// token retreival is independent of the verifications checked by these tests
describe('Authorizer Invalid Token Tests (TOKEN event)', function () {
    it('Missing ClientKey throws error for user token', async () => {
        const event = generateAuthorizerTokenEvent();
        const token = generateJwtToken('trial12');
        delete token.payload.clientkey;
        token.payload.scope = 'one-scope two-scope';
        mockOnceJwtDecodeAndVerify(token);
    
        await expect(authenticateToken(event, ['my-audience'], ['two-scope'], callDefaultOptions))
            .rejects.toThrowError('token does not have clientkey')
    });

    it('Invalid Scope in user token', async () => {
        const event = generateAuthorizerTokenEvent();
        const token = generateJwtToken('trial12');
        delete token.payload.clientkey;
        token.payload.scope = 'one-scope two-scope';
        mockOnceJwtDecodeAndVerify(token);

        await expect(authenticateToken(event, ['my-audience'], ['no-scope'], callDefaultOptions))
            .rejects.toThrowError('payload scope is not allowed')
    });

    it('Missing header in user token throws error', async () => {
        const event = generateAuthorizerTokenEvent();
        const token = generateJwtToken('trial12');
        delete token.header;
        mockOnceJwtDecodeAndVerify(token);

        await expect(authenticateToken(event, ['no-audience'], ['no-scope'], callDefaultOptions))
            .rejects.toThrowError('invalid token')
      })
    
      it('Missing header.kid in user token throws error', async () => {
        const event = generateAuthorizerTokenEvent();
        const token = generateJwtToken('trial12');
        delete token.header.kid;
        mockOnceJwtDecodeAndVerify(token);

        await expect(authenticateToken(event, ['no-audience'], ['no-scope'], callDefaultOptions))
            .rejects.toThrowError('invalid token')
      })
});