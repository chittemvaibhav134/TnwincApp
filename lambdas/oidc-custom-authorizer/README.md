# AWS API Gateway Custom Authorizer for RS256 JWTs

An AWS API Gateway [Custom Authorizer](http://docs.aws.amazon.com/apigateway/latest/developerguide/use-custom-authorizer.html) that authorizes API requests by requiring
that the OAuth2 [bearer token](https://tools.ietf.org/html/rfc6750) is a JWT that can be validated using the RS256 (asymmetric) algorithm with a public key that is obtained from a [JWKS](https://tools.ietf.org/html/rfc7517) endpoint.

## About

### What are "Custom Authorizers"?

In February 2016 Amazon
[announced](https://aws.amazon.com/blogs/compute/introducing-custom-authorizers-in-amazon-api-gateway/)
a new feature for API Gateway -
[Custom Authorizers](http://docs.aws.amazon.com/apigateway/latest/developerguide/use-custom-authorizer.html). This allows a Lambda function to be invoked prior to an API Gateway execution to perform custom authorization of the request, rather than using AWS's built-in authorization. This code can then be isolated to a single centralized Lambda function rather than replicated across every backend Lambda function.

### What does this Custom Authorizer do?

This package gives you the code for a custom authorizer that will, with a little configuration, perform authorization on AWS API Gateway requests via the following:

* It confirms that an OAuth2 bearer token has been passed via the `Authorization` header.
* It confirms that the token is a JWT that has been signed using the RS256 algorithm with a specific public key
* It obtains the public key by inspecting the configuration returned by a configured JWKS endpoint

## Setup

Install Node Packages:

```bash
npm install
```

This is a prerequisite for deployment as AWS Lambda requires these files to be included in a bundle (a special ZIP file).

## Local testing

Configure the local environment with a `.env` file by copying the sample:

```bash
cp .env.sample .env
```

### Environment Variables

Modify the `.env`:
* `JWKS_URI`: This is the URL of the associated JWKS endpoint in keycloak. The sample file as an example.

You can test the custom authorizer locally. You just need to obtain a valid JWT access token to perform the test. If you're using Auth0, see [these instructions](https://auth0.com/docs/tokens/access-token#how-to-get-an-access-token) on how to obtain one.

With a valid token, now you just need to create a local `event.json` file that contains it. Start by copying the sample file:

```bash
cp event.json.sample event.json
```

Then replace the `Authorization` text in that file with the JWT you obtained in the previous step.

You will also to replace the `Referer` text with a url that looks like `https://{baseurl}/{clientKey}`. This is how the code gets the client key from your request.

Finally, perform the test:

```bash
npm test
```

This uses the [lambda-local](https://www.npmjs.com/package/lambda-local) package to test the authorizer with your token. A successful test run will look something like this:

```
> lambda-local --timeout 300 --lambdapath index.js --eventpath event.json

Logs
----
START RequestId: fe210d1c-12de-0bff-dd0a-c3ac3e959520
{ type: 'REQUEST',
    headers:{ 'Authorization': 'Bearer eyJ0eXA...M2pdKi79742x4xtkLm6qNSdDYDEub37AI2h_86ifdIimY4dAOQ',
    'Referer' : 'https://admin.develop.navex-int.com/trial12/usermanager/import/manual/'
    }
    methodArn: 'arn:aws:execute-api:us-east-1:1234567890:apiId/stage/method/resourcePath' }
END


Message
------
{
    "principalId": "user_id",
    "policyDocument": {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "Stmt1459758003000",
                "Effect": "Allow",
                "Action": [
                    "execute-api:Invoke"
                ],
                "Resource": [
                    "arn:aws:execute-api:*"
                ]
            }
        ]
    }
}
```

An `Action` of `Allow` means the authorizer would have allowed the associated API call to the API Gateway if it contained your token.

## Deployment

Now we're ready to deploy the custom authorizer to an AWS API Gateway.

### Package template and deploy code to CloudFormation.

```aws cloudformation package --template template.authorizer.yml --s3-bucket $BucketName  --output-template auth.packaged.yml```

Navigate to the cloudfromation console and upload the auth.package.yml template to CloudFormation.

This will create the lambda function.

### Test the lambda function in AWS

1. Make sure your new lamdba function is open in the console, and from the **Actions** menu select `Configure test event`.

2. Copy the contents of your `event.json` file into the **Input test event** JSON.

3. Click **Save and test** to run the lambda.

You should see similar output to what you observed when [testing the lambda locally](#local-testing).

### Configure the Custom Authorizer in the API Gateway

1. In the [AWS API Gateway console](https://console.aws.amazon.com/apigateway/home) open an existing API, or optionally create a **New API**.

2. In the left panel, under your API name, click **Authorizers**.

3. Click **Create** > **Custom Authorizer**

4. Use the following values in the **New Custom Authorizer** form:
   * Lambda region: (same as lambda function created above)
   * Lambda function: `{Your Lambda funciton name or Arn}`
   * Authorizer name: `jwt-rsa-custom-authorizer`
   * Lambda Event Payload: `Request`
   * Identity Sources: `Authorization`, `Referer`
   * Result TTL in seconds: `3600`

5. Click **Create**

### Test the Custom Authorizer in the API Gateway

You can then test the new custom authorizer by providing an **Identity Token** and clicking **Test**. The ACCESS_TOKEN is the same format we used in `event.json` above:

```
Bearer ACCESS_TOKEN
```

A successful test will look something like:

```
Latency: 2270 ms
Principal Id: oauth|1234567890
Policy
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "Stmt1459758003000",
            "Effect": "Allow",
            "Action": [
                "execute-api:Invoke"
            ],
            "Resource": [
                "arn:aws:execute-api:*"
            ]
        }
    ]
}
```

### Configure API Gateway Resources to use the Custom Authorizer

1. In the left panel, under your API name, click **Resources**.

2. Under the Resource tree, select a specific resource and one of its Methods (eg. `GET`)

3. Select **Method Request**

4. Under the **Settings** section, click the pencil to the right of the **Authorization** and choose the `jwt-rsa-custom-authorizer` Custom Authorizer. Click the checkbox to the right of the drop down to save.

5. Make sure the **API Key Required** field is set to `false`

### Deploy the API Gateway

You need to Deploy the API to make the changes public.

1. Select the **Action** menu and choose **Deploy API**

2. When prompted for a stage, select or create a new stage (eg. `dev`).

3. In the stage, make note of the **Invoke URL**

### Test your API Gateway endpoint remotely

In the examples below:
* `INVOKE_URL` is the **Invoke URL** from the [Deploy the API Gateway](#deploy-the-api-gateway) section above
* `ACCESS_TOKEN` is the token in the `event.json` file
* `/your/resource` is the resource you secured in AWS API Gateway

#### With Postman

You can use Postman to test the REST API

* Method: (matching the Method in API Gateway, eg. `GET`)
* URL: `INVOKE_URL/your/resource`
* Headers tab: Add an `Authorization` header with the value `Bearer ACCESS_TOKEN`. Add a `Referer` header. 

---
