# Moonwatch Session SPI
This directory and below are the Moonwatch Session integration.
This builds an SPI for KeyCloak that calls Moonwatch after a LOGIN and LOGOUT events for a session.

It uses the Amazon SDK 2.x to make the calls to the Moonwatch API gateway.

## Configuration
Configuration is read through environment variables
### Local
Create a `secrets.env` in the repository root based on `secrets.env.sample`
### Deployed
Provide the required CFN template parameters to the `template.yml`  
This is currently piped through the `buildspec.tramsform.yml` file.

## Building and Contribuing
The build and packaging is all docker-based, so it not expected that there is any xplat drift.

## Note
*This project is a "linux-first" project. This means Windows-CLI specific instructions are not provided. For those wanting to use Windows, please work on this within WSL on a debian/ubtuntu based distro or map the steps to equivent facilities on your Windows environment.*

## Dependencies
* Docker!

## Recommended VS Code Extensions:
* @id:vscjava.vscode-java-pack
* @id:vscjava.vscode-maven
* The above require at least OpenJDK installed. Use the following to do so:
  ```
sudo apt update && sudo apt install msopenjdk-11
  ```

Information about using Launch Darkly SDK:  
https://docs.launchdarkly.com/sdk/server-side/java

Example used to derive the configuration for the SPI plugin:  
https://dev.to/adwaitthattey/building-an-event-listener-spi-plugin-for-keycloak-2044