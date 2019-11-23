# KeyCloak NAVEX developer install (manual edition)

This process allows a developer to manually install KeyCloak in a development environment. In the future, this process will be automated. Additionally, these processes allow for the sharing of KeyCloak configuration between developers.

## Installation

This process should only need to be completed once, unless the KeyCloak shared configuration has changed.

1. If KeyCloak has already been installed, [completely remove it](#removal) prior to reinstallation.
2. From `userstore/keycloak`:
```shell
docker-compose up -d
```

KeyCloak is now installed and accessible at http://localhost:8080. It is not yet configured. To configure, [import the configuration](#import-configuration).

## Removal

This process is destructive to any existing KeyCloak configuration. If you've made any local KeyCloak configuration changes that should be preserved, [export](#export-configuration) and commit them first.

1. From `userstore/keycloak`:
```shell
docker-compose down
docker volume rm keycloak_db
```

KeyCloak has now been completely removed.

## Export configuration

[Import/Export reference from the KeyCloak Manual](https://www.keycloak.org/docs/latest/server_admin/#_export_import)

PowerShell scripts have been created to help with import/export.

1. From `userstore/keycloak`, in PowerShell. Unfortunately, this step is not fully automated (yet). After running the following command, observe the log output and wait for a line of output similar to `Keycloak 8.0.0 (WildFly Core 10.0.0.Final) started in 19087ms - Started 684 of 989 services`, and then hit CTRL-C.
```powershell
.\Export-KeyCloakConfig.ps1
```
2. From `userstore/keycloak`:
```shell
docker-compose up -d
```
The exported configuration is now in `userstore/keycloak/import`. It should be committed to source control if any important changes have been made.

## Import configuration

[Import/Export reference from the KeyCloak Manual](https://www.keycloak.org/docs/latest/server_admin/#_export_import)

PowerShell scripts have been created to help with import/export.

1. From `userstore/keycloak`, in PowerShell. Unfortunately, this step is not fully automated (yet). After running the following command, observe the log output and wait for a line of output similar to `Keycloak 8.0.0 (WildFly Core 10.0.0.Final) started in 19087ms - Started 684 of 989 services`, and then hit CTRL-C.
```powershell
.\Import-KeyCloakConfig.ps1
```
2. From `userstore/keycloak`:
```shell
docker-compose up -d
```
After importing a fresh configuration, KC may throw an error message upon first login. If this happens, close the browser window and try again. It should work the second time.

## Miscellaneous notes

### Hostfile changes

HOSTS changes may be necessary. In general, any URL at which KC may need to be accessed should be added to the HOSTS file, e.g.:

```text
# KeyCloak Admin
keycloak.devlocal.navex-pe.com             127.0.0.1

# Client-specific KeyCloak URLs
trial12.keycloak.devlocal.navex-pe.com     127.0.0.1
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
