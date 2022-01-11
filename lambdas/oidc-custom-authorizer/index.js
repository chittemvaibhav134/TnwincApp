const lib = require('./lib');
let data;

// Lambda function index.handler - thin wrapper around lib.authenticate
module.exports.handler = async (event, context) => {
  try {
    console.log(event)
    console.log(context)
    data = await lib.authenticate(event);
  }
  catch (err) {
      console.log(err);
      return context.fail(`Unauthorized`);
  }
  return data;
};
