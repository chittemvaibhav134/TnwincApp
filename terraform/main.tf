terraform {
  required_providers {
    keycloak = {
      source = "mrparkers/keycloak"
      version = ">= 4.0.0"
    }
  }
}

provider "keycloak" {
    client_id     = "terraformclient"
    client_secret = "76216d2d-7bda-461b-9da3-4279922f5656"
    url           = "https://trial12.keycloak.devlocal.navex-pe.com:8443"
    base_path = "/auth"
}

