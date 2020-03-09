# platform-auth-keycloak/REST-samples

These samples illustrate proper and canonical NAVEX usage of the KeyCloak API.

## Prerequisites

* [Visual Studio Code](https://code.visualstudio.com/)
* The [REST Client vscode extension](https://marketplace.visualstudio.com/items?itemName=humao.rest-client)
* A KeyCloak instance with a `master` realm containing an administrative user with a known username and password, to be used to obtain `access_tokens`

## Basic Usage

Each `.rest` file contains variables which controls its operation. For example, `REST-samples/keycloak-deleteRealm.rest` has a `@realm = trial12` variable. This variable controls the ensuing REST calls; running the calls within this file with no changes will result in the `trial12` realm being deleted from KeyCloak.

The vscode workplace settings file `.vscode/settings.json` defines target environments. Currently, this file contains only a `local` environment, targeting a locally-installed KeyCloak instance. New environments can be added to this file and switched to using the command `REST Client: Switch Environment` (CTRL-ALT-E by default, also available as a button in the vscode status bar).

Each `.rest` file has a `login` operation defined at the top. It is necessary to execute this operation prior to executing any other operations, as it obtains the necessary `access_token` that the other operations depend on for authorization.

## Realm/Client/ClientScope particulars

Using the REST API to add a realm to KeyCloak works, but does not result in a fully-provisioned realm. To work fully, a realm requires clients (and likely client scopes.) In the current configuration, three operations must be executed in the following order to create a minimally-functional (for NAVEX development purposes) realm:

1. POST Realm (defined in `REST-samples/keycloak-postRealm.rest`): This operation adds a realm entity.
2. POST ClientScope (defined in `REST-samples/keycloak-postClientScope.rest`): This operation adds the necessary `doorman-mappings` client scope on which all NAVEX clients depend.
3. POST Client (defined in `REST-samples/keycloak-postClient.rest`): This operation adds a single client to a specified realm. This operation may need to be executed multiple times, depending on the details of the necessary clients.
