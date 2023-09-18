#!/usr/bin/env python

import argparse,json
from urllib3 import PoolManager
from xml.etree.ElementTree import fromstring as xml_fromstring
from typing import Any, List
import collections.abc


def load_json_file(file_path: str) -> dict:
    print(f"Loading JSON file from {file_path}")
    with open(file_path) as f:
        return json.load(f)

def save_dict_as_json(file_path: str, dictionary: dict) -> None:
    print(f"Saving dictionary as json file: {file_path}")
    with open(file_path, 'w') as f:
        json.dump(dictionary, f, indent=2)

def index_via_property_list(dictionary, properties: List[str]):
    """
    Indexes into dictionary via properties, which is just a list of the property names.
    Thus index_via_property_list(d, ["a","b","c"]) should be equivalent to d["a"]["b"]["c"]
    """
    for prop in properties:
        dictionary = dictionary[prop]
    return dictionary

def create_dict_from_prop_list(prop_list: List[str], value: Any) -> dict:
    dictionary = dict()
    for prop in reversed(prop_list):
        value = {prop: value}
        dictionary = value
    return dictionary

# yoinked from https://stackoverflow.com/a/3233356
def update(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = update(d.get(k, {}), v)
        else:
            d[k] = v
    return d

def update_client_property(realm_dict: dict, client_id: str, property: str, value: List[str], append: bool) -> None:
    value = value if isinstance(value, list) else [value]
    print(f"Searching for client id {client_id} in realm file...")
    client = next( c for c in realm_dict['clients'] if c['clientId'] == client_id )
    property_list = property.split(":")
    property_ref = index_via_property_list(client, property_list)
    is_prop_list = isinstance(property_ref, list)
    if not is_prop_list and len(value) < 2:
        print(f"Setting {client_id}:{property} to: {value[0]}")
        property_ref = value[0]
    elif is_prop_list and not append:
        print(f"Setting {client_id}:{property} to: {value}")
        property_ref = value
    elif is_prop_list and append:
        print(f"Appending {value} to existing {client_id}:{property} list...")
        property_ref = property_ref + value
    elif not is_prop_list and append:
        raise RuntimeError(f"append=True specified but {property} is not an array on the client object")
    elif not is_prop_list and len(value) > 1:
        raise RuntimeError(f"Multiple values passed in for client property {property} that is not a list")
    temp_dict = create_dict_from_prop_list(property_list, property_ref)
    update(client, temp_dict)


def update_sso_config(realm_dict: dict, idp_alias: str, metadata_url: str) -> None:
    http = PoolManager(cert_reqs='CERT_NONE', assert_hostname=False)
    print(f"Fetching metadata xml from: {metadata_url}")

    metadata_xml_string = http.request('GET', metadata_url).data.decode('utf-8')
    xml = xml_fromstring(metadata_xml_string)
    cert = xml.find('.//{http://www.w3.org/2000/09/xmldsig#}X509Certificate').text
    ss_out_uri = xml.find('.//{urn:oasis:names:tc:SAML:2.0:metadata}SingleLogoutService').attrib['Location']
    ss_in_uri = xml.find('.//{urn:oasis:names:tc:SAML:2.0:metadata}SingleSignOnService').attrib['Location']

    print(f"Searching for identityProvider with alias {idp_alias}...")
    idp = next( i for i in realm_dict['identityProviders'] if i['alias'] == idp_alias )
    print(f"Setting signingCertificate to: {cert}")
    idp['config']['signingCertificate'] = cert
    print(f"Setting singleLogoutServiceUrl to: {ss_out_uri}")
    idp['config']['singleLogoutServiceUrl'] = ss_out_uri
    print(f"Setting singleSignOnServiceUrl to: {ss_in_uri}")
    idp['config']['singleSignOnServiceUrl'] = ss_in_uri

def update_csp_header(realm_dict: dict, domains: List[str], prepend_wildcard: bool = False) -> None:
    domains = domains if isinstance(domains, list) else [domains]
    domains = [d.strip() for d in domains]
    if prepend_wildcard:
        print("Prefixing each domain with '*.'...")
        domains += [ f"*.{d}" for d in domains ]
    domain_str = f"frame-src 'self'; frame-ancestors 'self' {' '.join(domains)}; object-src 'none';"
    print(f"Setting contentSecurityPolicy to: {domain_str}")
    realm_dict['browserSecurityHeaders']['contentSecurityPolicy'] = domain_str

def disable_users(realm_dict: dict) -> None:
    for user in realm_dict['users']:
        if user.get('credentials',[]):
            print(f"Disabling user {user['username']}. FirstName '{user.get('firstName')}' LastName '{user.get('lastName')}'")
            user['enabled'] = False

if __name__== "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--realm-file", type=str, help="Path to realm file that needs to be transformed", required=True)
    parser.add_argument("-o", "--output-file", type=str, help="File to write transformed json to")
    parser.add_argument("-i", "--inplace-update", action='store_true', help="Save changes to realm file passed in")

    parser.add_argument("--disable-users", action='store_true', help="Disables hardcoded users from realm file")

    parser.add_argument("--idp-alias", type=str, help="identityProviders alias to update sso config from metadata url", required=False)
    parser.add_argument("--idp-metadata-url", type=str, help="Url to metadata of identity provider", required=False)

    parser.add_argument("--csp-header", type=str.lower, help="Comma delimited list of allowed domains", required=False)
    parser.add_argument("--wildcard-prefix", action='store_true', help="Prefix each domain with a *", required=False)

    parser.add_argument("--client-id", type=str, help="client name in realm file that needs transforming")
    parser.add_argument("-p", "--client-property", type=str, help="client property that needs to be set. ex: redirectUris, adminUrl")
    parser.add_argument("-v", "--client-value", type=str, action='append', help="List of values to set for a client property", default=[])
    parser.add_argument("--append", action='store_true', help="Add onto existing list; if not supplied the list is replaced")

    args = parser.parse_args()

    realm_dict = load_json_file(args.realm_file)
    print(f"Transforming keycloak v{realm_dict['keycloakVersion']} realm file: {args.realm_file}")

    if args.disable_users:
        print("Disabling hardcoded users from realm file...")
        disable_users(realm_dict)
    if args.idp_alias and args.idp_metadata_url:
        print("Transforming sso config...")
        update_sso_config(realm_dict, args.idp_alias, args.idp_metadata_url)
    else:
        print("Skipping sso config transform; required arguments not present")
    if args.csp_header:
        print("Transforming CSP header...")
        update_csp_header(realm_dict, args.csp_header.split(','), args.wildcard_prefix)
    else:
        print("Skipping CSP header transform; required arguments not present")
    if args.client_id and args.client_property and args.client_value:
        print("Transforming client property...")
        update_client_property(realm_dict, args.client_id, args.client_property, args.client_value, args.append)
    else:
        print("Skipping client property transform; required arguments not present")

    if args.output_file:
        save_dict_as_json(args.output_file, realm_dict)
    if args.inplace_update:
        save_dict_as_json(args.realm_file, realm_dict)
