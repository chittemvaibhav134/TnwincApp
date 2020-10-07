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
docker network create navexdev
docker-compose up -d --build
```

**It is important that you run the `network create` step. Keycloak now relies on an external network, so that it can be accessed by other containerized apps within the Navex Platform.**

KeyCloak is now installed and accessible at https://localhost:8443.
KeyCloak (IdP) is also installed and accessible at https://localhost:8444.

Alternatively, you can run dev-deploy on this repo and it will perform all the steps mentioned above.

## Adding user for KeyCloak (IdP)

Get the container ID for the Keycloak (IdP) process.
You can get a list of running processes with **docker ps**.

Look for the process which is running on port 8444. Remember this container ID.

In the **/opt/jboss/keycloak/bin/** folder there is a script called **add-user-keycloak.sh**
Run the add-user-keycloak shell script, by from the root of the repo, using the following command: docker exec [CONTAINER_ID] /opt/jboss/keycloak/bin/add-user-keycloak.sh -u [userName] -p [password]

Now you have a user you can log in on.
Navigate to https://localhost:8444 and log in with the new user/password you created above, and you should be able to use Keycloak as an IdP.

## Removal

This process is destructive to any existing KeyCloak configuration. If you've made any local KeyCloak configuration changes that should be preserved, [export](#export-configuration) and commit them first.

From the repo root:

```shell
docker-compose down
docker volume rm platform-auth-keycloak_db
docker network rm navexdev
```

KeyCloak has now been completely removed.

## Configuration Export

From the repo root, in PowerShell:

```powershell
.\Export-KeyCloakConfig.ps1
```

The exported configuration is now in the `import` directory. It should be committed to source control if any important changes have been made. NOTE: KeyCloak generates new IDs for most config elements during export. They will show up as diffs. This is annoying, but normal.

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

|username|password|purpose|
|---|---|---|
|`dvader`|`password`|Admin user|
