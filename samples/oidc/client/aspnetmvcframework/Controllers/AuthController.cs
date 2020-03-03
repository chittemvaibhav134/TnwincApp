using System;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text;
using System.Threading.Tasks;
using System.Web.Mvc;
using System.Web.Security;
using IdentityModel;
using IdentityModel.Client;
using Newtonsoft.Json;

namespace OIDCSpike.Controllers
{
    public class AuthController : Controller
    {
        private string[] _validDomains = new string[]
        {
            "oidcspike.devlocal.navex-pe.com"
        };

        // should come from config
        private string _oidcAuthUrlTemplate = "https://{0}.keycloak.devlocal.navex-pe.com:8443/auth/realms/navex/protocol/openid-connect/auth";
        private string _oidcTokenUrlTemplate = "https://{0}.keycloak.devlocal.navex-pe.com:8443/auth/realms/navex/protocol/openid-connect/token";
        private string _oidcClientId = "testClient";
        private string _oidcClientSecret = "ba0f147d-eeee-4536-9969-7bce81577adf";

        private string _redirectorPath = "OIDCSpike/Auth/CodeRedirector";
        private int _clockSkewSeconds = 60;

        public AuthController()
        {
            // turns off cert validation. only suitable for dev environments
            ServicePointManager.ServerCertificateValidationCallback +=
            (sender, certificate, chain, sslPolicyErrors) => true;
        }

        // Authn entry point. Configured with this bit in web.config:
        /*   <system.web>
               <authentication mode="Forms">
                 <forms loginUrl="~/Auth" timeout="2880" />
               </authentication>
             </system.web> */

        [AllowAnonymous]
        public ActionResult Index()
        {
            // exit early if we are already authenticated
            if (Request.IsAuthenticated)
            {
                return new RedirectResult("~/");
            }

            var clientSpecificUri = new ClientSpecificUri(Request.Url, _validDomains);
            var returnUrl = $"https://{clientSpecificUri.ClientKey}.{clientSpecificUri.StaticDomain}{Request.Params["ReturnUrl"]}";
            var redirectUri = GetRedirectUri(
                clientSpecificUri.StaticDomain,
                _redirectorPath,
                returnUrl);

            Session.Add("nonce", GetRandomString(32));
            var requestUrl = new RequestUrl(
                String.Format(_oidcAuthUrlTemplate,
                clientSpecificUri.ClientKey));
            var authRedirectUrl = requestUrl.CreateAuthorizeUrl(
                clientId: _oidcClientId,
                responseType: OidcConstants.ResponseTypes.Code,
                scope: OidcConstants.StandardScopes.OpenId,
                redirectUri: redirectUri,
                responseMode: OidcConstants.ResponseModes.Query,
                nonce: Session["nonce"].ToString(),
                state: Session.SessionID);

            return new RedirectResult(authRedirectUrl);
        }

        [AllowAnonymous]
        public ActionResult CodeRedirector()
        {
            var returnUri = new ClientSpecificUri(
                Request.Params["ReturnUrl"],
                _validDomains);

            var consumerPath = Request.CurrentExecutionFilePath
                .Replace(nameof(this.CodeRedirector), nameof(this.CodeConsumer));

            var builder = new StringBuilder($"http://{returnUri.ClientKey}");
            builder.Append($".{returnUri.StaticDomain}");
            builder.Append($"{consumerPath}");
            builder.Append($"?ReturnUrl={Uri.EscapeDataString(returnUri.ToString())}");
            builder.Append($"&state={Request.Params["state"]}");
            builder.Append($"&session_state={Request.Params["session_state"]}");
            builder.Append($"&code={Request.Params["code"]}");

            return new RedirectResult(builder.ToString());
        }

        [AllowAnonymous]
        public async Task<ActionResult> CodeConsumer()
        {
            var clientSpecificUri = new ClientSpecificUri(Request.Url, _validDomains);
            var redirectUri = GetRedirectUri(
                clientSpecificUri.StaticDomain,
                _redirectorPath,
                Uri.UnescapeDataString(Request["ReturnUrl"]));

            var client = new HttpClient();
            var response = await client.RequestAuthorizationCodeTokenAsync(new AuthorizationCodeTokenRequest
            {
                Address = String.Format(
                    _oidcTokenUrlTemplate,
                    clientSpecificUri.ClientKey),
                ClientId = _oidcClientId,
                ClientSecret = _oidcClientSecret,
                Code = Request["code"],
                RedirectUri = redirectUri
            });

            var nowDateTime = DateTime.UtcNow;

            Session["access_token"] = response.AccessToken;
            Session["id_token"] = response.IdentityToken;
            Session["refresh_token"] = response.RefreshToken;

            dynamic accessToken = JsonConvert.DeserializeObject(
                Encoding.UTF8.GetString(
                    Base64Url.Decode(
                        Session["access_token"].ToString().Split('.')[1])));

            // token nonce must match the nonce we original set
            if ((string)accessToken.nonce != Session["nonce"].ToString())
            {
                throw new Exception("Token nonce does not match original nonce.");
            }

            // token client key must match current url
            if ((string)accessToken.clientkey != clientSpecificUri.ClientKey)
            {
                throw new Exception("token clientkey does not match clientkey in url.");
            }

            // nbf must not be in the future
            var nbfDateTime = DateTimeOffset
                .FromUnixTimeSeconds((long)accessToken.nbf)
                .ToUniversalTime()
                .AddSeconds(-_clockSkewSeconds);
            if (nbfDateTime > nowDateTime)
            {
                throw new Exception("token's nbf (not before) time is in the future");
            }

            // exp must not be in the past
            var expDateTime = DateTimeOffset
                .FromUnixTimeSeconds((long)accessToken.exp)
                .ToUniversalTime()
                .AddSeconds(_clockSkewSeconds);
            if (expDateTime < nowDateTime)
            {
                throw new Exception($"token's exp (expiry) time is in the past");
            }

            FormsAuthentication.SetAuthCookie((string)accessToken.preferred_username, false);

            return new RedirectResult(Request["ReturnUrl"]);
        }

        private string GetRedirectUri(string staticDomain, string path, string returnUrl)
        {
            return $"http://{staticDomain}/{path}?ReturnUrl={Uri.EscapeDataString(returnUrl)}";
        }

        private static string GetRandomString(int bytes)
        {
            string token;
            using (RandomNumberGenerator rng = new RNGCryptoServiceProvider())
            {
                byte[] tokenData = new byte[bytes];
                rng.GetBytes(tokenData);
                token = Convert.ToBase64String(tokenData);
            }
            return token;
        }

        private class ClientSpecificUri : Uri
        {
            public string[] ValidDomains { get; set; }

            public string ClientKey =>
                Host.Substring(0, Host.IndexOf(StaticDomain) - 1);

            public string StaticDomain =>
                ValidDomains.Single(d => Host.EndsWith(d));

            public ClientSpecificUri(Uri uri, string[] validDomains)
                : this(uri.ToString(), validDomains) { }

            public ClientSpecificUri(string uriString, string[] validDomains)
                : base(uriString)
            {
                ValidDomains = validDomains;
            }


        }
    }
}
