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

	#create external navexdev network. This way containerized platform apps can share a network with 
	#keycloak 
	$dockerNetworks = docker network ls
	if (-Not ($dockerNetworks -match 'navexdev')){
		docker network create navexdev
	}

	# remove existing instance if it exists
	docker-compose -f docker-compose.yml down;
	docker volume rm platform-auth-keycloak_db
	docker-compose -f docker-compose-idp.yml down
	docker volume rm platform-auth-keycloak_keycloak-idp-db

	# spin up new instance
	docker-compose -f docker-compose.yml up -d --build
	docker-compose -f docker-compose-idp.yml up -d --build
}.GetNewClosure();
