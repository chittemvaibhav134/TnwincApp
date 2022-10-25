resource "keycloak_realm" "navex_realm"  {
    realm = "navex_realm"
    enabled = true
    display_name = "navex_realm"

    security_defenses {
        headers {
            content_security_policy = "frame-src 'self'; frame-ancestors 'self' *.navex-pe.com:* https://doorman.dev.gw.local *.pt.dev.local:*; object-src 'none';"
        }
    }
}

data "keycloak_openid_client_scope" "profile" {
    realm_id = keycloak_realm.navex_realm.id
    name = "profile"
}
//  CANT DO THIS
resource "keycloak_openid_user_property_protocol_mapper" "username_property_mapper"{
    realm_id = keycloak_realm.navex_realm.id
    client_scope_id = data.keycloak_openid_client_scope.profile.id
    name = "username"
    user_property = "username"
    claim_name = "puid"
}