$repoRoot = Resolve-Path (Join-Path "$PSScriptRoot" "..\") | Select-Object -ExpandProperty Path

New-CreateHostEntry -Domain "keycloak.devlocal.navex-pe.com" -IpAddress "127.0.0.1" -Enforce -Comment "Keycloak no subdomain"
New-CreateHostEntry -Domain "aperturelabs.keycloak.devlocal.navex-pe.com" -IpAddress "127.0.0.1" -Enforce -Comment "Aperture Labs KeyCloak support"
New-CreateHostEntry -Domain "trial11.keycloak.devlocal.navex-pe.com" -IpAddress "127.0.0.1" -Enforce -Comment "Trial11 KeyCloak support"
New-CreateHostEntry -Domain "trial12.keycloak.devlocal.navex-pe.com" -IpAddress "127.0.0.1" -Enforce -Comment "Trial12 KeyCloak support"

# Import Keycloak cert to avoid manually clicking Advanced -> Continue when automation testing
# Import-Certificate won't re-add the certificate if it already exists
New-ExecutableToCall -Name "KeyCloak Cert" -WorkingDirectory $repoRoot -Tag PreBuild -ScriptBlock {
	$certPath = (Join-Path $repoRoot "build\app\fs\etc\x509\https\tls.crt");
	Import-Certificate -FilePath $certPath -CertStoreLocation Cert:\LocalMachine\Root;
	Import-Certificate -FilePath $certPath -CertStoreLocation Cert:\LocalMachine\My;
}.GetNewClosure();

New-ExecutableToCall -Name "Start Keycloak" -WorkingDirectory $repoRoot -Tag PreBuild -ScriptBlock {
	IF (-Not (Get-Command "docker" -errorAction SilentlyContinue))
	{
		throw "Local Keycloak requires Docker Desktop to be installed"
	}

	# remove existing instance if it exists
	docker-compose down;
	docker volume rm platform-auth-keycloak_db;

	# spin up new instance
	docker-compose up -d --build;
}.GetNewClosure();