
export function isStringArray(arr: any): arr is string[] {
    if (!Array.isArray(arr)) { throw new Error('arr must be an array') }
    return arr.reduce(function(i, s) { return typeof(s) !== 'string' ? i + 1 : i  }, 0) === 0
}