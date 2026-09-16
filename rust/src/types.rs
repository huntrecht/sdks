//! Shared response shapes for the Huntrecht Platform API v1.
//!
//! Fully-typed structs cover the hot paths (auth, orders); the remaining
//! resources decode into [`serde_json::Value`] so new API fields never break
//! the client.
use serde::{Deserialize, Serialize};

/// OAuth2 token response (`POST /auth/token`).
#[derive(Debug, Clone, Deserialize)]
pub struct TokenResponse {
    pub access_token: String,
    #[serde(default)]
    pub token_type: String,
    #[serde(default)]
    pub expires_in: i64,
    #[serde(default)]
    pub refresh_token: Option<String>,
    #[serde(default)]
    pub scope: String,
}

/// A B2B order.
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Order {
    #[serde(default)]
    pub id: String,
    #[serde(default)]
    pub commodity: String,
    #[serde(flatten)]
    pub extra: std::collections::HashMap<String, serde_json::Value>,
}

/// Paginated order list.
#[derive(Debug, Clone, Deserialize)]
pub struct OrderList {
    #[serde(default)]
    pub data: Vec<Order>,
}
