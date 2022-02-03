import { isStringArray } from "./util";


const COMPLEXITY_LIMIT = 500

/**
 *  Verifies the payloadScope is one of allowedScopes, throws if it is unable to verify.
 * @param allowedScopes The list of allowed/accepted scopes for the endpoint this is protecting
 * @param payloadScope The unparsed list of scopes from the OIDC JWT.
 */
export function verifyScope(allowedScopes: Set<string>, payloadScope: string, complexityLimit: number = COMPLEXITY_LIMIT): void {
    if (allowedScopes.size === 0) { throw new Error('allowedScopes cannot be an empty array') }

    if (typeof(payloadScope) === 'string') {
        let countOfSpaces = 0;
        for(const char of payloadScope) {
            countOfSpaces += char == ' ' ? 1 : 0
        }
        const countOfPayloadScopes = payloadScope.length > 0 ? countOfSpaces + 1 : 0

        if( countOfPayloadScopes * allowedScopes.size > complexityLimit ) {
            throw new Error(`payload scope has too many elements, complexity above limit ${complexityLimit}`)
        }

        for (const scope of new Set<string>(payloadScope.split(' '))) {
            if (allowedScopes.has(scope)) {
                return;
            }
        }
        throw new Error('payload scope is not allowed')
    } else {
        throw new Error('payload scope was not a string')
    }
} 