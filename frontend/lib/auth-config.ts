import type { Configuration, PopupRequest } from "@azure/msal-browser";

const tenantId = process.env.NEXT_PUBLIC_ENTRA_TENANT_ID?.trim() ?? "";
const webClientId = process.env.NEXT_PUBLIC_ENTRA_WEB_CLIENT_ID?.trim() ?? "";
const apiClientId = process.env.NEXT_PUBLIC_ENTRA_API_CLIENT_ID?.trim() ?? "";

export const entraConfigError = [
  ["NEXT_PUBLIC_ENTRA_TENANT_ID", tenantId],
  ["NEXT_PUBLIC_ENTRA_WEB_CLIENT_ID", webClientId],
  ["NEXT_PUBLIC_ENTRA_API_CLIENT_ID", apiClientId]
]
  .filter(([, value]) => !value)
  .map(([name]) => name);

export const apiAccessScope = `api://${apiClientId}/access_as_user`;

export const msalConfig: Configuration = {
  auth: {
    clientId: webClientId || "missing-entra-web-client-id",
    authority: `https://login.microsoftonline.com/${tenantId || "missing-entra-tenant-id"}`,
    redirectUri: "http://localhost:3000/",
    postLogoutRedirectUri: "http://localhost:3000/"
  },
  cache: {
    cacheLocation: "sessionStorage"
  }
};

export const loginRequest: PopupRequest = {
  scopes: [apiAccessScope]
};
