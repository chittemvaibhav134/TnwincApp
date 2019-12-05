## Deployspec
[deployspec.json](./deployspec.json) pattern/file is doucmented in confluence [here](https://confluence.navexglobal.com/display/PE/Deployspec)
* Only needing the stack name from an aws-inf deploy so that it can hook into a vpc and some existing networking infrastructure

## Buildspecs
Consumed by the aws service codebuild. File structure can be referenced [here](https://docs.aws.amazon.com/codebuild/latest/userguide/build-spec-ref.html)
Having buildspecs live with the code allow build/deploy processes to travel with the code they effect instead of needing a corrdinated pipeline update for all changes.
### buildspec.yml
[buildspec.yml](./buildspec.yml) creates needed build artifacts for this project and does some low level validation for both codepipeline and github PRs
* In the future the PR bit of this will most likely be broken into a seperate file or certain commands will be gated by an env var
    * For now though there is so little going on here that i think the DRY violation isn't worth the clarity
* Creates a [template-configuration.json](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/continuous-delivery-codepipeline-cfn-artifacts.html#w2ab1c13c17c15) file with the KeyCloakImage value as the sole artifact
    * Right now this is just a hardcoded value, but there was talk about mirroring the kc image to ecr and if we build it from this repo the image uri would most likely get generated from this file so I think this is a good place to generate the value for future proofing our build requirements
### buildspec.transform.yml
[buildspec.transform.yml](./buildspec.transform.yml) is a wonky thing that lets the deployment pipeline hand execution back to something that lives with the code with some deploy time artifact files so that transforms can be done however code sees fit.
* Creates another [template-configuration.json](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/continuous-delivery-codepipeline-cfn-artifacts.html#w2ab1c13c17c15) with the `InfrastructureStackName` (gotten from deployment context by codepipeline) parameter and some cfn tags that we should put on the stack.
    * The project name tag could be applied during the build as well, but since version isn't gettable at that point i think it makes more sense here

## Cloudformation templates
[cloudformation templates](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-reference.html) are json/yml files that describe aws resources for infrastructure-as-code goals

### pipeline.develop.yml
[pipeline.develop.yml](./pipeline.develop.yml) creates the needed build/deploy bits in aws to track the `develop` branch of this repo. At this time updates to this file need to be manually mirrored to the tools aws account by someone in devops. If changes are needed make them in the PR that requires the updates and ping devops to review and corrdinate the update before merging
* This specifically deploys keycloak to unstable integration environments
    * Just wobbly for right now
* Will probably copy/paste this into pipeline.stable.yml in the nearish future and update the deploy accounts
    * is a massive DRY problem, but templating this template has proved a bit terrible and i can't tell which is the least bad solution

### Readme
This very [readme.md](./readme.md)