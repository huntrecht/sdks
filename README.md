# Huntrecht Platform SDK — v1

Official SDKs for the Huntrecht Platform API v1. All SDKs share a common protobuf schema definition for consistent types across languages.

## Architecture

```
sdk/
├── proto/huntrecht/v1/core.proto    # Single source of truth for all types
├── Makefile                         # `make generate` → protoc → all languages
├── python/                          # huntrecht-sdk (PyPI)
├── typescript/                      # @huntrecht/sdk (npm)
├── go/                              # github.com/huntrecht/sdk-go
├── ruby/                            # huntrecht-sdk (RubyGems)
└── rust/                            # huntrecht-sdk (crates.io)
```

## Available SDKs

| Language | Package | Status |
|----------|---------|--------|
| Python | `huntrecht-sdk` | ✅ v0.1.0 |
| TypeScript/JavaScript | `@huntrecht/sdk` | ✅ v0.1.0 |
| Go | `github.com/huntrecht/sdk-go` | 🚧 Coming Soon |
| Ruby | `huntrecht-sdk` | 🚧 Coming Soon |
| Rust | `huntrecht-sdk` | 🚧 Coming Soon |

## API Coverage (v1)

All SDKs cover the complete Platform API v1 surface — **41 endpoints** across **13 resource groups**:

| Resource | Endpoints | Scope |
|----------|-----------|-------|
| `auth` | 2 | Token, revoke |
| `clients` | 5 | API client CRUD, rotate secret |
| `orders` | 3 | List, get, create |
| `payments` | 3 | List, get, create |
| `subscriptions` | 2 | List, get |
| `credit` | 2 | Assess, score |
| `kyc` | 3 | List, get, submit |
| `quotes` | 3 | List, get, create |
| `users` | 2 | Me, get by ID |
| `storefront` | 5 | Collections, products, search |
| `priceDrops` | 2 | List, featured (public) |
| `appProxy` | 4 | Shopify theme proxy |
| `linkedPayments` | 4 | Eligibility, link wallet/bank |

## Quick Start (Python)

```bash
pip install huntrecht-sdk
```

```python
from huntrecht import HuntrechtClient

client = HuntrechtClient(
    client_id="hnt_your_client_id",
    client_secret="your_secret"
)

# Authenticate
tokens = client.auth.token()
print(f"Access token expires in {tokens['expires_in']}s")

# List orders
orders = client.orders.list(status="pending")
for order in orders["data"]:
    print(f"Order {order['id']}: {order['commodity']}")

# Get credit score
score = client.credit.score("customer@example.com")
print(f"Score: {score['data']['credit_score']}")
```

## Quick Start (TypeScript)

```bash
npm install @huntrecht/sdk
```

```typescript
import { HuntrechtClient } from '@huntrecht/sdk';

const client = new HuntrechtClient({
  clientId: 'hnt_your_client_id',
  clientSecret: 'your_secret',
});

// Authenticate
const tokens = await client.auth.token();
console.log(`Access token expires in ${tokens.expires_in}s`);

// List orders
const orders = await client.orders.list({ status: 'pending' });
for (const order of orders.data) {
  console.log(`Order ${order.id}: ${order.commodity}`);
}

// Get credit score
const score = await client.credit.score('customer@example.com');
console.log(`Score: ${score.data.credit_score}`);
```

## Authentication

All SDKs use OAuth2 Client Credentials flow:

1. Create an API client in your dashboard or via `client.clients.create()`
2. Use the `client_id` and `client_secret` to initialize the SDK
3. The SDK automatically obtains and refreshes tokens

```python
# Python — automatic auth on first request
client = HuntrechtClient(client_id="hnt_abc", client_secret="secret")
orders = client.orders.list()  # token obtained automatically
```

```typescript
// TypeScript — automatic auth on first request
const client = new HuntrechtClient({ clientId: 'hnt_abc', clientSecret: 'secret' });
const orders = await client.orders.list();  // token obtained automatically
```

## Rate Limits

Rate limits are enforced by your subscription plan:

| Plan | Requests/Minute |
|------|----------------|
| Starter | 60 |
| Basic | 300 |
| Standard | 1,000 |
| Pro | 3,000 |
| Enterprise | 10,000 |

All SDKs handle 429 responses automatically with exponential backoff.

## Error Handling

```python
from huntrecht import HuntrechtError, RateLimitError, AuthenticationError

try:
    orders = client.orders.list()
except AuthenticationError as e:
    print(f"Auth failed: {e}")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except HuntrechtError as e:
    print(f"API error: {e} (status={e.status_code})")
```

```typescript
import { HuntrechtError, RateLimitError, AuthenticationError } from '@huntrecht/sdk';

try {
  const orders = await client.orders.list();
} catch (error) {
  if (error instanceof AuthenticationError) {
    console.error('Auth failed:', error.message);
  } else if (error instanceof RateLimitError) {
    console.error(`Rate limited. Retry after ${error.retryAfter}s`);
  } else if (error instanceof HuntrechtError) {
    console.error(`API error: ${error.message} (status=${error.status})`);
  }
}
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `HUNTRECHT_BASE_URL` | API base URL (default: `https://api.huntrecht.com`) |
| `HUNTRECHT_CLIENT_ID` | OAuth2 client ID |
| `HUNTRECHT_CLIENT_SECRET` | OAuth2 client secret |

## Generating SDKs from Protobuf

```bash
cd sdk
make generate          # Generate all language types
make generate-python   # Python only
make generate-typescript  # TypeScript only
```

## License

MIT
