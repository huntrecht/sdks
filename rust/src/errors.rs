//! Error types for the Huntrecht SDK.
use thiserror::Error;

/// Errors returned by the Huntrecht Platform API.
#[derive(Debug, Error)]
pub enum HuntrechtError {
    /// 401 — missing, expired, or invalid credentials.
    #[error("authentication failed: {0}")]
    AuthenticationError(String),
    /// 429 — rate limited; `retry_after` carries the Retry-After seconds.
    #[error("rate limited, retry after {retry_after}s: {message}")]
    RateLimitError { message: String, retry_after: u64 },
    /// 404 — resource not found.
    #[error("not found: {0}")]
    NotFoundError(String),
    /// 422 — request validation failed.
    #[error("validation failed: {0}")]
    ValidationError(String),
    /// 403 — authenticated but not permitted.
    #[error("permission denied: {0}")]
    PermissionError(String),
    /// Any other HTTP failure.
    #[error("request failed (HTTP {status}): {message}")]
    HttpError { status: u16, message: String },
    /// Transport-level failure (timeouts, DNS, TLS…).
    #[error("transport error: {0}")]
    TransportError(String),
    /// Response body was not valid JSON.
    #[error("invalid response: {0}")]
    DecodeError(String),
}

/// 401 — re-exported for parity with the other SDKs.
pub type AuthenticationError = HuntrechtError;
/// 429 — re-exported for parity with the other SDKs.
pub type RateLimitError = HuntrechtError;
