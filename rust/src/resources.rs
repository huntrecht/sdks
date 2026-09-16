//! Resource APIs for the Huntrecht Platform API v1.
//!
//! Mirrors the Python / TypeScript / Go SDKs: same paths, same query
//! parameters, same JSON bodies. Hot paths use typed structs
//! ([`crate::types`]); everything else decodes to [`serde_json::Value`].
use reqwest::Method;
use serde_json::{json, Value};

use crate::client::{body, opt, q, Client, Map};
use crate::errors::HuntrechtError;
use crate::types::{Order, TokenResponse};

/// OAuth2 token lifecycle.
pub struct AuthApi<'a> {
    pub(crate) client: &'a Client,
}

impl AuthApi<'_> {
    /// Exchange client credentials for tokens.
    pub async fn token(&self) -> Result<TokenResponse, HuntrechtError> {
        self.client
            .request_raw(
                Method::POST,
                "/auth/token",
                &[],
                Some(body(&[
                    ("grant_type", json!("client_credentials")),
                    ("client_id", json!(self.client.client_id())),
                    ("client_secret", json!(self.client.client_secret())),
                ])),
                false,
            )
            .await
    }
    /// Revoke a token.
    pub async fn revoke(&self, token: &str) -> Result<Value, HuntrechtError> {
        self.client
            .request(Method::POST, "/auth/revoke", &q(&[("token", opt(token))]), None, false)
            .await
    }
}

/// OAuth2 API clients.
pub struct ClientsApi<'a> {
    pub(crate) client: &'a Client,
}

impl ClientsApi<'_> {
    /// List API clients for a user.
    pub async fn list(&self, user_id: i64) -> Result<Value, HuntrechtError> {
        self.client
            .request(Method::GET, "/clients", &q(&[("user_id", Some(user_id.to_string()))]), None, true)
            .await
    }
    /// Create an API client (secret returned only once).
    pub async fn create(&self, user_id: i64, data: Value) -> Result<Value, HuntrechtError> {
        self.client
            .request(Method::POST, "/clients", &q(&[("user_id", Some(user_id.to_string()))]), Some(data), true)
            .await
    }
    /// Rotate an API client's secret.
    pub async fn rotate_secret(&self, user_id: i64, client_id: &str) -> Result<Value, HuntrechtError> {
        let path = format!("/clients/{client_id}/rotate");
        self.client
            .request(Method::POST, &path, &q(&[("user_id", Some(user_id.to_string()))]), None, true)
            .await
    }
    /// Delete an API client.
    pub async fn delete(&self, user_id: i64, client_id: &str) -> Result<Value, HuntrechtError> {
        let path = format!("/clients/{client_id}");
        self.client
            .request(Method::DELETE, &path, &q(&[("user_id", Some(user_id.to_string()))]), None, true)
            .await
    }
}

fn page_params(page: i64, per_page: i64, status: Option<&str>) -> Vec<(&'static str, String)> {
    q(&[
        ("page", Some(page.to_string())),
        ("per_page", Some(per_page.to_string())),
        ("status", status.map(str::to_string)),
    ])
}

/// B2B orders.
pub struct OrdersApi<'a> {
    pub(crate) client: &'a Client,
}

impl OrdersApi<'_> {
    /// List paginated orders.
    pub async fn list(&self, page: i64, per_page: i64, status: Option<&str>) -> Result<Value, HuntrechtError> {
        self.client.request(Method::GET, "/orders", &page_params(page, per_page, status), None, true).await
    }
    /// Get one order.
    pub async fn get(&self, order_id: &str) -> Result<Order, HuntrechtError> {
        let path = format!("/orders/{order_id}");
        let wrapper: Map = self.client.request(Method::GET, &path, &[], None, true).await?;
        let order = wrapper.get("data").cloned().unwrap_or(Value::Null);
        serde_json::from_value(order).map_err(|e| HuntrechtError::DecodeError(e.to_string()))
    }
    /// Place a new order.
    pub async fn create(&self, params: &[(&str, String)], data: Value) -> Result<Value, HuntrechtError> {
        self.client.request(Method::POST, "/orders", params, Some(data), true).await
    }
}

/// Payments.
pub struct PaymentsApi<'a> {
    pub(crate) client: &'a Client,
}

impl PaymentsApi<'_> {
    /// List paginated payments.
    pub async fn list(&self, page: i64, per_page: i64, status: Option<&str>) -> Result<Value, HuntrechtError> {
        self.client.request(Method::GET, "/payments", &page_params(page, per_page, status), None, true).await
    }
    /// Get one payment.
    pub async fn get(&self, payment_id: &str) -> Result<Value, HuntrechtError> {
        let path = format!("/payments/{payment_id}");
        self.client.request(Method::GET, &path, &[], None, true).await
    }
    /// Record a new payment.
    pub async fn create(&self, data: Value) -> Result<Value, HuntrechtError> {
        self.client.request(Method::POST, "/payments", &[], Some(data), true).await
    }
}

/// B2B subscriptions.
pub struct SubscriptionsApi<'a> {
    pub(crate) client: &'a Client,
}

impl SubscriptionsApi<'_> {
    /// List paginated subscriptions.
    pub async fn list(&self, page: i64, per_page: i64, status: Option<&str>, include_history: bool) -> Result<Value, HuntrechtError> {
        let mut query = page_params(page, per_page, status);
        query.push(("include_payment_history", include_history.to_string()));
        self.client.request(Method::GET, "/subscriptions", &query, None, true).await
    }
    /// Get one subscription.
    pub async fn get(&self, subscription_id: &str) -> Result<Value, HuntrechtError> {
        let path = format!("/subscriptions/{subscription_id}");
        self.client.request(Method::GET, &path, &[], None, true).await
    }
}

/// Basic credit scoring.
pub struct CreditApi<'a> {
    pub(crate) client: &'a Client,
}

impl CreditApi<'_> {
    /// Run a credit assessment.
    pub async fn assess(&self, data: Value) -> Result<Value, HuntrechtError> {
        self.client.request(Method::POST, "/credit/assess", &[], Some(data), true).await
    }
    /// Score a customer email.
    pub async fn score(&self, customer_email: &str) -> Result<Value, HuntrechtError> {
        let path = format!("/credit/score/{customer_email}");
        self.client.request(Method::GET, &path, &[], None, true).await
    }
}

/// Risk scoring, company assessments, improvement, credit history.
pub struct CreditRiskApi<'a> {
    pub(crate) client: &'a Client,
}

impl CreditRiskApi<'_> {
    /// Risk score for a customer.
    pub async fn get_score(&self, customer_id: &str) -> Result<Value, HuntrechtError> {
        self.client
            .request(Method::GET, "/credit-risk/score", &q(&[("customer_id", opt(customer_id))]), None, true)
            .await
    }
    /// Request a risk assessment.
    pub async fn assess(&self, data: Value) -> Result<Value, HuntrechtError> {
        self.client.request(Method::POST, "/credit-risk/assess", &[], Some(data), true).await
    }
    /// Connected credit history.
    pub async fn get_history(&self, customer_id: &str, limit: i64) -> Result<Value, HuntrechtError> {
        self.client
            .request(Method::GET, "/data-connect/credit-history",
                &q(&[("customer_id", opt(customer_id)), ("limit", Some(limit.to_string()))]), None, true)
            .await
    }
    /// Company credit assessment.
    pub async fn get_assessment(&self, user_id: &str) -> Result<Value, HuntrechtError> {
        self.client
            .request(Method::GET, "/company/credit-assessment", &q(&[("user_id", opt(user_id))]), None, true)
            .await
    }
    /// Open a new company assessment.
    pub async fn request_assessment(&self, data: Value) -> Result<Value, HuntrechtError> {
        self.client.request(Method::POST, "/company/credit-assessment/request", &[], Some(data), true).await
    }
    /// Credit-improvement options.
    pub async fn get_improvement_options(&self) -> Result<Value, HuntrechtError> {
        self.client.request(Method::GET, "/credit-improvement/available-options", &[], None, true).await
    }
    /// Link a wallet for credit improvement.
    pub async fn connect_wallet(&self, data: Value) -> Result<Value, HuntrechtError> {
        self.client.request(Method::POST, "/credit-improvement/connect-wallet", &[], Some(data), true).await
    }
    /// Apply credit-improvement boosts.
    pub async fn apply_boosts(&self, data: Value) -> Result<Value, HuntrechtError> {
        self.client.request(Method::POST, "/credit-improvement/apply-boosts", &[], Some(data), true).await
    }
}

/// KYC submissions.
pub struct KycApi<'a> {
    pub(crate) client: &'a Client,
}

impl KycApi<'_> {
    /// List paginated submissions.
    pub async fn list(&self, page: i64, per_page: i64, status: Option<&str>) -> Result<Value, HuntrechtError> {
        self.client.request(Method::GET, "/kyc", &page_params(page, per_page, status), None, true).await
    }
    /// Get one submission.
    pub async fn get(&self, submission_id: &str) -> Result<Value, HuntrechtError> {
        let path = format!("/kyc/{submission_id}");
        self.client.request(Method::GET, &path, &[], None, true).await
    }
    /// File a new submission.
    pub async fn submit(&self, data: Value) -> Result<Value, HuntrechtError> {
        self.client.request(Method::POST, "/kyc", &[], Some(data), true).await
    }
}

/// Commodity quotes.
pub struct QuotesApi<'a> {
    pub(crate) client: &'a Client,
}

impl QuotesApi<'_> {
    /// Get one quote.
    pub async fn get(&self, quote_id: &str) -> Result<Value, HuntrechtError> {
        let path = format!("/quotes/{quote_id}");
        self.client.request(Method::GET, &path, &[], None, true).await
    }
    /// Request a new quote.
    pub async fn create(&self, data: Value) -> Result<Value, HuntrechtError> {
        self.client.request(Method::POST, "/quotes", &[], Some(data), true).await
    }
}

/// User profiles.
pub struct UsersApi<'a> {
    pub(crate) client: &'a Client,
}

impl UsersApi<'_> {
    /// Calling user.
    pub async fn me(&self) -> Result<Value, HuntrechtError> {
        self.client.request(Method::GET, "/users/me", &[], None, true).await
    }
    /// One user.
    pub async fn get(&self, user_id: &str) -> Result<Value, HuntrechtError> {
        let path = format!("/users/{user_id}");
        self.client.request(Method::GET, &path, &[], None, true).await
    }
}

/// Shopify-backed catalog.
pub struct StorefrontApi<'a> {
    pub(crate) client: &'a Client,
}

impl StorefrontApi<'_> {
    /// List collections.
    pub async fn collections(&self, first: i64, include_products: bool) -> Result<Value, HuntrechtError> {
        self.client
            .request(Method::GET, "/storefront/collections",
                &q(&[("first", Some(first.to_string())), ("include_products", Some(include_products.to_string()))]), None, true)
            .await
    }
    /// One collection with products.
    pub async fn collection(&self, handle: &str, products_first: i64) -> Result<Value, HuntrechtError> {
        let path = format!("/storefront/collections/{handle}");
        self.client
            .request(Method::GET, &path, &q(&[("products_first", Some(products_first.to_string()))]), None, true)
            .await
    }
    /// List products.
    pub async fn products(&self, first: i64, after: Option<&str>, b2b_only: bool) -> Result<Value, HuntrechtError> {
        self.client
            .request(Method::GET, "/storefront/products",
                &q(&[("first", Some(first.to_string())), ("after", after.map(str::to_string)), ("b2b_only", Some(b2b_only.to_string()))]), None, true)
            .await
    }
    /// One product.
    pub async fn product(&self, handle: &str) -> Result<Value, HuntrechtError> {
        let path = format!("/storefront/products/{handle}");
        self.client.request(Method::GET, &path, &[], None, true).await
    }
    /// Search the catalog.
    pub async fn search(&self, query: &str, first: i64, b2b_only: bool) -> Result<Value, HuntrechtError> {
        self.client
            .request(Method::GET, "/storefront/search",
                &q(&[("query", opt(query)), ("first", Some(first.to_string())), ("b2b_only", Some(b2b_only.to_string()))]), None, true)
            .await
    }
}

/// Price-drop events (public).
pub struct PriceDropsApi<'a> {
    pub(crate) client: &'a Client,
}

impl PriceDropsApi<'_> {
    /// Recent drops.
    pub async fn list(&self, limit: i64, min_discount: f64, days: i64) -> Result<Value, HuntrechtError> {
        self.client
            .request(Method::GET, "/price-drops",
                &q(&[("limit", Some(limit.to_string())), ("min_discount", Some(min_discount.to_string())), ("days", Some(days.to_string()))]), None, false)
            .await
    }
    /// Headline drops.
    pub async fn featured(&self, limit: i64) -> Result<Value, HuntrechtError> {
        self.client
            .request(Method::GET, "/price-drops/featured", &q(&[("limit", Some(limit.to_string()))]), None, false)
            .await
    }
}

/// Theme-safe proxy endpoints (public).
pub struct AppProxyApi<'a> {
    pub(crate) client: &'a Client,
}

impl AppProxyApi<'_> {
    /// Proxied collections.
    pub async fn collections(&self, first: i64, signature: Option<&str>) -> Result<Value, HuntrechtError> {
        self.client
            .request(Method::GET, "/app-proxy/collections",
                &q(&[("first", Some(first.to_string())), ("signature", signature.map(str::to_string))]), None, false)
            .await
    }
    /// One proxied collection.
    pub async fn collection(&self, handle: &str, first: i64, signature: Option<&str>) -> Result<Value, HuntrechtError> {
        let path = format!("/app-proxy/collections/{handle}");
        self.client
            .request(Method::GET, &path,
                &q(&[("first", Some(first.to_string())), ("signature", signature.map(str::to_string))]), None, false)
            .await
    }
    /// Proxied drops.
    pub async fn price_drops(&self, limit: i64, min_discount: f64) -> Result<Value, HuntrechtError> {
        self.client
            .request(Method::GET, "/app-proxy/price-drops",
                &q(&[("limit", Some(limit.to_string())), ("min_discount", Some(min_discount.to_string()))]), None, false)
            .await
    }
    /// Eligible B2B payment methods.
    pub async fn payment_methods(&self, customer_id: Option<&str>, product_price: f64, b2b_exclusive: bool, signature: Option<&str>) -> Result<Value, HuntrechtError> {
        self.client
            .request(Method::GET, "/app-proxy/payment-methods",
                &q(&[("customer_id", customer_id.map(str::to_string)), ("product_price", Some(product_price.to_string())), ("b2b_exclusive", Some(b2b_exclusive.to_string())), ("signature", signature.map(str::to_string))]), None, false)
            .await
    }
}

/// Linked wallets and bank accounts.
pub struct LinkedPaymentsApi<'a> {
    pub(crate) client: &'a Client,
}

impl LinkedPaymentsApi<'_> {
    /// Eligibility check (public).
    pub async fn check_eligibility(&self, customer_id: &str, product_price: f64, b2b_exclusive: bool) -> Result<Value, HuntrechtError> {
        self.client
            .request(Method::GET, "/linked-payments/check-eligibility",
                &q(&[("customer_id", opt(customer_id)), ("product_price", Some(product_price.to_string())), ("b2b_exclusive", Some(b2b_exclusive.to_string()))]), None, false)
            .await
    }
    /// Link a crypto wallet.
    pub async fn link_wallet(&self, data: Value) -> Result<Value, HuntrechtError> {
        self.client.request(Method::POST, "/linked-payments/link-wallet", &[], Some(data), true).await
    }
    /// Link a bank account via Plaid.
    pub async fn link_bank(&self, data: Value) -> Result<Value, HuntrechtError> {
        self.client.request(Method::POST, "/linked-payments/link-bank", &[], Some(data), true).await
    }
    /// Customer's linked accounts.
    pub async fn linked_accounts(&self, customer_id: &str) -> Result<Value, HuntrechtError> {
        let path = format!("/linked-payments/linked-accounts/{customer_id}");
        self.client.request(Method::GET, &path, &[], None, true).await
    }
}

/// Re-exported for the doc example (`orders.data`, `order.id`…).
pub use crate::types::OrderList;
