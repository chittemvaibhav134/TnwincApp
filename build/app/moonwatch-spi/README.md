This project is a "linux-first" project. This means Windows-CLI instructions are not provided. For those wanting to use Windows, please work on this within WSL on a debian/ubtuntu based distro.

The build and packaging is all docker-based, so there should not be any xplat drift in that regard.

Dependencies
* Docker!



Recommended VS Code Extensions:
* @id:vscjava.vscode-java-pack
* @id:vscjava.vscode-maven
* The above require at least OpenJDK installed. Use the following to do so:
  ```
sudo apt update && sudo apt install msopenjdk-11
  ```

https://docs.launchdarkly.com/sdk/server-side/java
https://dev.to/adwaitthattey/building-an-event-listener-spi-plugin-for-keycloak-2044