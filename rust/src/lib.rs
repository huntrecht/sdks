/// Huntrecht Platform SDK for Rust
///
/// Official client for the Huntrecht Platform API v1.
///
/// # Example
///
/// ```no_run
/// use huntrecht::Client;
///
/// #[tokio::main]
/// async fn main() -> Result<(), Box<dyn std::error::Error>> {
///     let client = Client::builder()
///         .client_id("hnt_your_client_id")
///         .client_secret("your_secret")
///         .build()?;
///
///     let orders = client.orders().list().await?;
///     for order in orders.data {
///         println!("Order {}: {}", order.id, order.commodity);
///     }
///     Ok(())
/// }
/// ```

pub mod client;
pub mod errors;
pub mod types;
pub mod resources;

pub use client::Client;
pub use errors::{HuntrechtError, AuthenticationError, RateLimitError};
