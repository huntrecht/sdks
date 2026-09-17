//! Core HTTP client: auth, retries, rate-limit handling, resources.
use std::collections::HashMap;
use std::sync::Mutex;
use std::time::{Duration, Instant};

use reqwest::header::{HeaderMap, HeaderValue};
use serde_json::Value;

use crate::errors::HuntrechtError;
use crate::resources;

const API_VERSION: &str = "v1";
const DEFAULT_BASE_URL: &str = "https://api.huntrecht.com";
const USER_AGENT: &str = concat!("huntrecht-sdk-rs/", env!("CARGO_PKG_VERSION"));

/// Builder for [`Client`].
#[derive(Default)]
pub struct Builder {
    base_url: Option<String>,
    client_id: Option<String>,
    client_secret: Option<String>,
    access_token: Option<String>,
    timeout: Option<Duration>,
    max_retries: Option<u32>,
}

impl Builder {
    /// Override the API base URL (`HUNTRECHT_BASE_URL` env otherwise).
    pub fn base_url(mut self, url: impl Into<String>) -> Self {
        self.base_url = Some(url.into());
        self
    }
    /// OAuth2 client id (`HUNTRECHT_CLIENT_ID` env otherwise).
    pub fn client_id(mut self, id: impl Into<String>) -> Self {
        self.client_id = Some(id.into());
        self
    }
    /// OAuth2 client secret (`HUNTRECHT_CLIENT_SECRET` env otherwise).
    pub fn client_secret(mut self, secret: impl Into<String>) -> Self {
        self.client_secret = Some(secret.into());
        self
    }
    /// Pre-existing access token (skips the token exchange).
    pub fn access_token(mut self, token: impl Into<String>) -> Self {
        self.access_token = Some(token.into());
        self
    }
    /// Request timeout (default 30s).
    pub fn timeout(mut self, timeout: Duration) -> Self {
        self.timeout = Some(timeout);
        self
    }
    /// Max retries on 5xx/429 (default 3).
    pub fn max_retries(mut self, n: u32) -> Self {
        self.max_retries = Some(n);
        self
    }
    /// Build the client.
    pub fn build(self) -> Result<Client, HuntrechtError> {
        let timeout = self.timeout.unwrap_or(Duration::from_secs(30));
        let http = reqwest::Client::builder()
            .timeout(timeout)
            .build()
            .map_err(|e| HuntrechtError::TransportError(e.to_string()))?;
        Ok(Client {
            base_url: self
                .base_url
                .or_else(|| std::env::var("HUNTRECHT_BASE_URL").ok())
                .unwrap_or_else(|| DEFAULT_BASE_URL.to_string())
                .trim_end_matches('/')
                .to_string(),
            client_id: self
                .client_id
                .or_else(|| std::env::var("HUNTRECHT_CLIENT_ID").ok())
                .unwrap_or_default(),
            client_secret: self
                .client_secret
                .or_else(|| std::env::var("HUNTRECHT_CLIENT_SECRET").ok())
                .unwrap_or_default(),
            http,
            timeout,
            max_retries: self.max_retries.unwrap_or(3),
            token: Mutex::new(self.access_token.map(|t| TokenState {
                access: t,
                refresh: None,
                expires_at: Instant::now() + Duration::from_secs(3600),
            })),
        })
    }
}

#[allow(dead_code)]
struct TokenState {
    access: String,
    refresh: Option<String>,
    expires_at: Instant,
}

/// Huntrecht Platform API client (v1).
pub struct Client {
    base_url: String,
    client_id: String,
    client_secret: String,
    http: reqwest::Client,
    timeout: Duration,
    max_retries: u32,
    token: Mutex<Option<TokenState>>,
}

impl Client {
    /// Start building a client.
    pub fn builder() -> Builder {
        Builder::default()
    }

    /// OAuth2 client id (crate-internal; resources need it for token calls).
    pub(crate) fn client_id(&self) -> &str {
        &self.client_id
    }

    /// OAuth2 client secret (crate-internal).
    pub(crate) fn client_secret(&self) -> &str {
        &self.client_secret
    }

    /// Current User-Agent (tracks `Cargo.toml` via `CARGO_PKG_VERSION`).
    pub fn user_agent() -> &'static str {
        USER_AGENT
    }

    // ---- resource accessors (mirror the Python/TS/Go SDKs) ----
    pub fn auth(&self) -> resources::AuthApi<'_> { resources::AuthApi { client: self } }
    pub fn clients(&self) -> resources::ClientsApi<'_> { resources::ClientsApi { client: self } }
    pub fn orders(&self) -> resources::OrdersApi<'_> { resources::OrdersApi { client: self } }
    pub fn payments(&self) -> resources::PaymentsApi<'_> { resources::PaymentsApi { client: self } }
    pub fn subscriptions(&self) -> resources::SubscriptionsApi<'_> { resources::SubscriptionsApi { client: self } }
    pub fn credit(&self) -> resources::CreditApi<'_> { resources::CreditApi { client: self } }
    pub fn credit_risk(&self) -> resources::CreditRiskApi<'_> { resources::CreditRiskApi { client: self } }
    pub fn kyc(&self) -> resources::KycApi<'_> { resources::KycApi { client: self } }
    pub fn quotes(&self) -> resources::QuotesApi<'_> { resources::QuotesApi { client: self } }
    pub fn users(&self) -> resources::UsersApi<'_> { resources::UsersApi { client: self } }
    pub fn storefront(&self) -> resources::StorefrontApi<'_> { resources::StorefrontApi { client: self } }
    pub fn price_drops(&self) -> resources::PriceDropsApi<'_> { resources::PriceDropsApi { client: self } }
    pub fn app_proxy(&self) -> resources::AppProxyApi<'_> { resources::AppProxyApi { client: self } }
    pub fn linked_payments(&self) -> resources::LinkedPaymentsApi<'_> { resources::LinkedPaymentsApi { client: self } }

    async fn ensure_token(&self) -> Result<(), HuntrechtError> {
        if let Ok(guard) = self.token.lock() {
            if let Some(state) = guard.as_ref() {
                if state.expires_at > Instant::now() {
                    return Ok(());
                }
            }
        }
        if self.client_id.is_empty() || self.client_secret.is_empty() {
            return Err(HuntrechtError::AuthenticationError(
                "No access token and no client credentials. Set HUNTRECHT_CLIENT_ID and HUNTRECHT_CLIENT_SECRET.".into(),
            ));
        }
        let tokens = self.auth().token().await?;
        let mut guard = self.token.lock().map_err(|e| HuntrechtError::TransportError(e.to_string()))?;
        *guard = Some(TokenState {
            access: tokens.access_token.clone(),
            refresh: tokens.refresh_token.clone(),
            expires_at: Instant::now() + Duration::from_secs(tokens.expires_in.max(120) as u64 - 60),
        });
        Ok(())
    }

    pub(crate) async fn request<T: serde::de::DeserializeOwned>(
        &self,
        method: reqwest::Method,
        path: &str,
        query: &[(&str, String)],
        body: Option<Value>,
        auth_required: bool,
    ) -> Result<T, HuntrechtError> {
        if auth_required {
            self.ensure_token().await?;
        }
        self.request_raw(method, path, query, body, auth_required).await
    }

    /// Request without the token-exchange preamble (breaks the
    /// request → ensure_token → token → request async cycle).
    pub(crate) async fn request_raw<T: serde::de::DeserializeOwned>(
        &self,
        method: reqwest::Method,
        path: &str,
        query: &[(&str, String)],
        body: Option<Value>,
        auth_required: bool,
    ) -> Result<T, HuntrechtError> {
        let mut attempts = 0;
        let mut last_error: Option<HuntrechtError> = None;
        loop {
            let mut url = format!("{}/api/{}{}", self.base_url, API_VERSION, path);
            if !query.is_empty() {
                let qs: Vec<String> = query.iter().map(|(k, v)| format!("{k}={v}")).collect();
                url.push('?');
                url.push_str(&qs.join("&"));
            }
            let mut headers = HeaderMap::new();
            headers.insert("Accept", HeaderValue::from_static("application/json"));
            headers.insert("User-Agent", HeaderValue::from_static(USER_AGENT));
            if auth_required {
                let bearer: Option<String> = self.token.lock().ok()
                    .and_then(|guard| guard.as_ref().map(|state| format!("Bearer {}", state.access)));
                if let Some(token) = bearer {
                    if let Ok(value) = HeaderValue::from_str(&token) {
                        headers.insert("Authorization", value);
                    }
                }
            }
            let mut req = self.http.request(method.clone(), &url).headers(headers);
            if let Some(b) = body.clone() {
                req = req.json(&b);
            }
            req = req.timeout(self.timeout);
            match self.http.execute(req.build().map_err(|e| HuntrechtError::TransportError(e.to_string()))?).await {
                Ok(resp) => {
                    let status = resp.status();
                    if status == reqwest::StatusCode::TOO_MANY_REQUESTS && attempts < self.max_retries {
                        attempts += 1;
                        let wait = resp.headers().get("Retry-After")
                            .and_then(|v| v.to_str().ok())
                            .and_then(|v| v.parse::<u64>().ok())
                            .unwrap_or(1 << attempts);
                        tokio::time::sleep(Duration::from_secs(wait)).await;
                        continue;
                    }
                    if status.is_server_error() && attempts < self.max_retries {
                        attempts += 1;
                        tokio::time::sleep(Duration::from_secs(1 << attempts.min(5))).await;
                        continue;
                    }
                    return self.handle_response(status, resp).await;
                }
                Err(e) if attempts < self.max_retries => {
                    attempts += 1;
                    last_error = Some(HuntrechtError::TransportError(e.to_string()));
                    tokio::time::sleep(Duration::from_secs(1 << attempts.min(5))).await;
                }
                Err(e) => {
                    return Err(last_error.unwrap_or_else(||
                        HuntrechtError::TransportError(e.to_string())));
                }
            }
        }
    }

    async fn handle_response<T: serde::de::DeserializeOwned>(
        &self,
        status: reqwest::StatusCode,
        resp: reqwest::Response,
    ) -> Result<T, HuntrechtError> {
        if status == reqwest::StatusCode::NO_CONTENT {
            let empty = serde_json::from_value(Value::Object(Default::default()))
                .map_err(|e| HuntrechtError::DecodeError(e.to_string()))?;
            return Ok(empty);
        }
        let text = resp.text().await.map_err(|e| HuntrechtError::TransportError(e.to_string()))?;
        let data: Value = serde_json::from_str(&text).unwrap_or(Value::String(text.clone()));
        if !status.is_success() {
            let msg = data.get("error_description").and_then(|v| v.as_str())
                .unwrap_or(&text).chars().take(300).collect::<String>();
            let msg = if msg.is_empty() { format!("HTTP {status}") } else { msg };
            return Err(match status.as_u16() {
                401 => {
                    if let Ok(mut guard) = self.token.lock() {
                        *guard = None;
                    }
                    HuntrechtError::AuthenticationError(msg)
                }
                403 => HuntrechtError::PermissionError(msg),
                404 => HuntrechtError::NotFoundError(msg),
                422 => HuntrechtError::ValidationError(msg),
                429 => HuntrechtError::RateLimitError { message: msg, retry_after: 60 },
                _ => HuntrechtError::HttpError { status: status.as_u16(), message: msg },
            });
        }
        serde_json::from_value(data).map_err(|e| HuntrechtError::DecodeError(e.to_string()))
    }
}

/// Query pairs helper for resources.
pub(crate) fn q<'a>(pairs: &[(&'a str, Option<String>)]) -> Vec<(&'a str, String)> {
    pairs.iter().filter_map(|(k, v)| v.clone().map(|s| (*k, s))).collect()
}

/// Optional string helpers.
pub fn opt(v: impl Into<String>) -> Option<String> {
    let s = v.into();
    if s.is_empty() { None } else { Some(s) }
}

/// Serialize a JSON map body.
pub fn body(pairs: &[(&str, Value)]) -> Value {
    let mut map = serde_json::Map::new();
    for (k, v) in pairs {
        map.insert((*k).to_string(), v.clone());
    }
    Value::Object(map)
}

/// HashMap alias used across resources.
pub type Map = HashMap<String, Value>;
