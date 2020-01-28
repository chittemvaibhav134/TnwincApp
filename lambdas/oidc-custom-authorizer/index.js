const lib = require('./lib');
let data;

// Lambda function index.handler - thin wrapper around lib.authenticate
module.exports.handler = async (event) => {
  try {
    data = await lib.authenticate(event);
    await lib.authorize(event);
  }
  catch (err) {
      console.log(err);
      return `Unauthorized: ${err.message}`;
  }
  return data;
};
