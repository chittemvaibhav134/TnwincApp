# dev-mock

This is a configuration of KeyCloak that serves as a local authentication stub. It contains the following users:

client  | username  | password   | PUID                                 | role
------- | --------- | ---------- | ------------------------------------ | -------------------
navex   | `dvader`  | `password` | 00000000-0000-0000-0000-000000000006 | Navex Admin user
trial12 | `shiva`   | `test1`    | C785A0FB-8B1A-E511-AF9F-00155D103480 | Platform Admin user
trial12 | `okenobi` | `password` | 00000000-0000-0000-0000-000000000066 | platform user

NOTE: The [original JIRA story](https://jira.navexglobal.com/browse/SSO-6913) requesting this configuration included, as can be seen above, a "client" value for each user. However, the issue with this is that KeyCloak has no concept of "client" in the way that it's expressed here. "Client" is a NAVEX concept. We access KeyCloak at `<clientkey>.<keycloakhost>`, but this is just a convenience to allow Doorman to detect the client authentication context by deriving it from the Referer header. The `<clientkey>` value in the url does not influence KeyCloak behavior in any way. So all the users listed in the table here will exist at whatever URL KeyCloak is accessed from.

TL;DR: If any behavior depends on the nonexistence of any of these users based on the `<clientkey>` value in the KeyCloak URL, it will fail.
