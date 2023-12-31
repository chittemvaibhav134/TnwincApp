# platform-auth-keycloak

This process allows a developer to install KeyCloak in a development environment.

## Dependencies

* Docker
* Docker Compose
* [jq](https://stedolan.github.io/jq/) (if you intend to export configuration)

> In Windows, both Docker and Docker Compose are included with the Docker Desktop install.

## Installation

This process should only need to be performed once, unless the KeyCloak shared configuration has changed. If KeyCloak has already been installed, [completely remove it](#removal) prior to reinstallation.

From the repo root:

```shell
# *nix environments
touch secrets.env
# Powershell environments
New-Item -Path secrets.env -ItemType File -ErrorAction SilentlyContinue
# All environments
docker network create navexdev
docker-compose -f docker-compose.yml up -d --build
docker-compose -f docker-compose-idp.yml up -d --build
```

**It is important that you run the `network create` step. Keycloak now relies on an external network, so that it can be accessed by other containerized apps within the Navex Platform.**

KeyCloak is now installed and accessible at https://localhost:8443.
KeyCloak (IdP) is also installed and accessible at https://localhost:8444.

Alternatively, you can run dev-deploy on this repo and it will perform all the steps mentioned above.

## Adding user for KeyCloak (IdP)

Get the container ID for the Keycloak (IdP) process.
You can get a list of running processes with **docker ps**.

Look for the process which is running on port 8444. Remember this container ID.

First, get into the docker container using the ID you just obtained, with the command **docker exec -it <container name> /bin/bash** to get a bash shell
In the **/opt/jboss/keycloak/bin/** folder there is a script called **add-user-keycloak.sh**
Run the add-user-keycloak shell script, by from the root of the repo, using the following command: docker exec [CONTAINER_ID] /opt/jboss/keycloak/bin/add-user-keycloak.sh -u [userName] -p [password]

Now you have a user you can log in on.
Navigate to https://localhost:8444 and log in with the new user/password you created above, and you should be able to use Keycloak as an IdP.

## Getting metadata
To get the metadata, ensure you have an hostfile entry (C:\Windows\system32\drivers\etc\hosts) which loops back to localhost for 
https://keycloak.devlocal.navex-pe.com

Then navigate to 
https://keycloak.devlocal.navex-pe.com:8444/auth/realms/master/protocol/saml/descriptor
and you should be ready to add an IdP in Platform.

## Removal

This process is destructive to any existing KeyCloak configuration. If you've made any local KeyCloak configuration changes that should be preserved, [export](#export-configuration) and commit them first.

From the repo root:

```shell
docker-compose -f docker-compose.yml down
docker volume rm platform-auth-keycloak_db
docker-compose -f docker-compose-idp.yml down
docker volume rm platform-auth-keycloak_keycloak-idp-db	
docker network rm navexdev
```

KeyCloak has now been completely removed.

## Upgrade

Pull the branch that contains the desired version. Run DevDeploy.

## Configuration Export

From the repo root, in PowerShell:

```powershell
.\Export-KeyCloakConfig.ps1 -containerName keycloak-app -composeFilePath .\docker-compose.yml
.\Export-KeyCloakConfig.ps1 -containerName keycloak-idp -composeFilePath .\docker-compose-idp.yml
```

The exported configuration is now in the `import` directory. It should be committed to source control if any important changes have been made. NOTE: KeyCloak generates new IDs for most config elements during export. They will show up as diffs. This is annoying, but normal.

## SNS Topic

Microservices can subscribe to the output ```RotateSecretTopicArn``` in order to receive messages when Keycloak secrets are rotated. The new secrets can be retrieved from SSM. Example message:
```
{
    "Type": "Notification",
    "MessageId": "f8509f8f-9ba0-57d6-a76b-c6b259f2499f",
    "TopicArn": "arn:aws:sns:us-west-2:455920928861:keycloak-psychic-potato-RotateSecretTopic-FX36U8LR4R02",
    "Subject": null,
    "Message": "A Keycloak secret has been rotated",
    "Timestamp": "2021-06-11T19:57:06.807Z",
    "SignatureVersion": "1",
    "Signature": "GyrZLpOYPVD1gM7cwmY1r407sBHMcj0Lo4kmxKKeEdKxtPGV8zHWDpg9k3rMrCrYSlKPs2qmIL+8hjJBBnaH3HNgAPF5msjDkag6zM77+oUK76VjQUODoDO3nYAJbziQ8gzJowPOMkqjKtGbnYtOHHhq4I4MkHg0XE+/et569LJDTgQa17iZvk9HyLfg6s9gk4lLv5ib3Nep8ooO69WG6vDPrbmKMB6ZUhM7LZ9fn4hOSyEb1K4Xloj2pxe54FrD28fElQaTcv/rid7UcPEdgKyKGfwnSYjs6kqJjczT/2Smtyu9mKjdJ2AmLdUnS1OhsVNrAA7FltexhVXrSjtKLg==",
    "SigningCertUrl": "https://sns.us-west-2.amazonaws.com/SimpleNotificationService-010a507c1833636cd94bdb98bd93083a.pem",
    "UnsubscribeUrl": "https://sns.us-west-2.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-west-2:455920928861:keycloak-psychic-potato-RotateSecretTopic-FX36U8LR4R02:0bda2f10-20d2-4469-bcb9-51692dff7396",
    "MessageAttributes": {
        "clientId": {
            "Type": "String",
            "Value": "workato"
        },
        "realmName": {
            "Type": "String",
            "Value": "navex"
        },
        "ssmPath": {
            "Type": "String",
            "Value": "/keycloak-psychic-potato/client-keys/navex/workato"
        }
    }
}
```

## Miscellaneous notes

### Hostfile changes

HOSTS changes may be necessary. In general, any URL at which KC may need to be accessed should be added to the HOSTS file, e.g.:

```text
# KeyCloak Admin
127.0.0.1             keycloak.devlocal.navex-pe.com

# Client-specific KeyCloak URLs
127.0.0.1             trial12.keycloak.devlocal.navex-pe.com
```

Your configuration may differ depending on which local client keys you typically work with.

### Viewing/monitoring KeyCloak logs

To output all KeyCloak logs:

```shell
docker logs keycloak-app
```

Add an `-f` to the `logs` command to follow the logs in real time:

```shell
docker logs -f keycloak-app
```

### Shared configuration details

#### Users

| username | password   | purpose    |
| -------- | ---------- | ---------- |
| `dvader` | `password` | Admin user |
