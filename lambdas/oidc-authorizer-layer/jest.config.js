/** @type {import('ts-jest/dist/types').InitialOptionsTsJest} */
// module.exports =
export default
{
  preset: 'ts-jest',
  testEnvironment: 'node',
  testPathIgnorePatterns : ['/node_modules/', '/output/'],
  testMatch: ['**/?(*.)+(spec|test).[jt]s?(x)']
};