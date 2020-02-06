# keycloak/aws-inf
​
## Deployspec
​
The [deployspec.json](./deployspec.json) pattern/file is documented in Confluence [here](https://confluence.navexglobal.com/display/PE/Deployspec).
​
* As of now the only dependency this has for deploying is on a really wonky repo called `aws-inf` ( https://github.com/tnwinc/aws-inf/blob/stable/template.yml ). I have it consuming the outputs on that stack directly from CloudFormation as cross-stack exports, so the only thing needed from the deployment context is the actual name of the stack it is snagging exports from. Example here: https://github.com/tnwinc/platform-auth-keycloak/blob/develop/template.yml#L83
​
## Buildspecs
​
Buildspecs are consumed by AWS CodeBuild. The buildspec file structure is documented [here](https://docs.aws.amazon.com/codebuild/latest/userguide/build-spec-ref.html).
Storing buildspecs with the code allows build/deploy processes to travel with the code they affect instead of needing a coordinated pipeline update for all changes.
​
### buildspec.yml
​
[buildspec.yml](./buildspec.yml) creates needed build artifacts for this project and does some low level validation for both AWS CodePipeline and GitHub PRs.
​
* Creates a [template-configuration.json](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/continuous-delivery-codepipeline-cfn-artifacts.html#w2ab1c13c17c15) file with the `KeyCloakImage` value as the sole artifact
  * Right now this is just a hardcoded value, but there was talk about mirroring the KC image to ECR. If we build it from this repo, the image URI would most likely get generated from this file, so I think this is a good place to generate the value for future-proofing our build requirements
* In the future, we will want to take different actions depending on whether the build was triggered by a PR against `develop` or a merge into `master`. The PR-triggered actions will most likely be broken into a seperate file, or, alternatively, certain commands will be gated by an environment variable. While splitting into separate files would make the files easier to read and understand, it also would mean we might have to remember to change things in two places.
​
### buildspec.transform.yml
​
[buildspec.transform.yml](./buildspec.transform.yml) lets the deployment pipeline hand execution back to something that lives with the code, along with some deploy-time artifact files. This allows additional transforms to be done however the code sees fit.
​
* Creates another [template-configuration.json](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/continuous-delivery-codepipeline-cfn-artifacts.html#w2ab1c13c17c15) file with the `InfrastructureStackName` parameter (retrieved from the deployment context by CodePipeline), along with some CloudFormation tags, to be put on the stack.
  * The `ProjectName` tag could be applied during the build as well, but since version isn't available at that point in the process, I think it makes more sense to put it here.
​
## CloudFormation templates
​
[CloudFormation templates](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-reference.html) are JSON or YAML files that describe deployable AWS resources, allowing us to describe our infrastructure as code.
​
### pipeline.develop.yml
​
[pipeline.develop.yml](./pipeline.develop.yml) creates the needed build/deploy bits in AWS to track the `develop` branch of this repo. At this time, updates to this file need to be manually mirrored to the Tools AWS account by someone in DevOps. If changes are needed, create a PR and ping DevOps to review and coordinate the update prior to merging.
​
* This deploys KeyCloak to unstable integration environments--just Wobbly for now
* I will probably duplicate this into pipeline.stable.yml soon and update the deploy accounts
  * This is a massive DRY problem, but templating this template has proved a bit terrible, and I can't tell which is the least bad solution
​
### README.md
​
This very [README.md](./README.md).
