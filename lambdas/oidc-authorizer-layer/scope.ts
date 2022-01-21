import { areAllElementsStrings } from "./util";

const COMPLEXITY_LIMIT = 500

/** Verifies the payloadScope is one of allowedScopes, throws if it is unable to verify. */
export function verifyScope(allowedScopes: string[], payloadScope: string): void {
    if (allowedScopes.length === 0) { throw new Error('allowedScopes cannot be an empty array') }
    if (typeof(payloadScope) === 'string') {
        const scopes = payloadScope.split(' ', COMPLEXITY_LIMIT / allowedScopes.length)
        if (scopes.reduce( (i, s) => i + s.length, 0) + scopes.length - 1 < payloadScope.length) {
            throw new Error(`payload scope has too many elements, complexity above limit ${COMPLEXITY_LIMIT}`)
        }
        const isFound = allowedScopes.find( val => scopes.find(s => s === val) !== undefined ) !== undefined
        if (!isFound) { throw new Error('payload scope is not allowed') }
    } else {
        throw new Error('payload scope was not a string or string array')
    }
} 