/**
 * Huntrecht Platform API Client — v1
 *
 * Core HTTP client with automatic token management, retry logic,
 * rate-limit handling, and typed resource access.
 * Works in Node.js 18+ and browsers (uses native fetch).
 */

import {
  HuntrechtError,
  AuthenticationError,
  RateLimitError,
  NotFoundError,
  ValidationError,
  PermissionError,
} from './errors.js';

const API_VERSION = 'v1';
const DEFAULT_BASE_URL = 'https://api.huntrecht.com';

export interface HuntrechtClientOptions {
  /** API base URL. Defaults to HUNTRECHT_BASE_URL env or https://api.huntrecht.com */
  baseUrl?: string;
  /** OAuth2 client ID. Defaults to HUNTRECHT_CLIENT_ID env. */
  clientId?: string;
  /** OAuth2 client secret. Defaults to HUNTRECHT_CLIENT_SECRET env. */
  clientSecret?: string;
  /** Pre-existing access token (skips auth if provided). */
  accessToken?: string;
  /** Request timeout in ms. Default 30000. */
  timeout?: number;
  /** Max retry attempts on 5xx/429. Default 3. */
  maxRetries?: number;
  /** Base backoff in ms for retries. Default 1000. */
  retryBackoff?: number;
}

interface RequestInitWithRetry extends RequestInit {
  maxRetries?: number;
}

export class HuntrechtClient {
  readonly baseUrl: string;
  readonly clientId: string;
  readonly clientSecret: string;
  readonly timeout: number;
  readonly maxRetries: number;
  readonly retryBackoff: number;

  _accessToken: string | null = null;
  _refreshToken: string | null = null;
  private _tokenExpiresAt = 0;

  // Resource accessors
  readonly auth: AuthAPI;
  readonly clients: ClientsAPI;
  readonly orders: OrdersAPI;
  readonly payments: PaymentsAPI;
  readonly subscriptions: SubscriptionsAPI;
  readonly credit: CreditAPI;
  readonly kyc: KycAPI;
  readonly quotes: QuotesAPI;
  readonly users: UsersAPI;
  readonly storefront: StorefrontAPI;
  readonly priceDrops: PriceDropsAPI;
  readonly appProxy: AppProxyAPI;
  readonly linkedPayments: LinkedPaymentsAPI;

  constructor(options: HuntrechtClientOptions = {}) {
    this.baseUrl = (options.baseUrl ?? processEnv('HUNTRECHT_BASE_URL') ?? DEFAULT_BASE_URL).replace(/\/+$/, '');
    this.clientId = options.clientId ?? processEnv('HUNTRECHT_CLIENT_ID') ?? '';
    this.clientSecret = options.clientSecret ?? processEnv('HUNTRECHT_CLIENT_SECRET') ?? '';
    this.timeout = options.timeout ?? 30000;
    this.maxRetries = options.maxRetries ?? 3;
    this.retryBackoff = options.retryBackoff ?? 1000;

    if (options.accessToken) {
      this._accessToken = options.accessToken;
    }

    // Lazy resource instantiation via dynamic import to avoid circular deps
    const r = createResources(this);
    this.auth = r.auth;
    this.clients = r.clients;
    this.orders = r.orders;
    this.payments = r.payments;
    this.subscriptions = r.subscriptions;
    this.credit = r.credit;
    this.kyc = r.kyc;
    this.quotes = r.quotes;
    this.users = r.users;
    this.storefront = r.storefront;
    this.priceDrops = r.priceDrops;
    this.appProxy = r.appProxy;
    this.linkedPayments = r.linkedPayments;
  }

  /** Make an API request with automatic auth, retry, and rate-limit handling. */
  async request<T = unknown>(
    method: string,
    path: string,
    options: {
      params?: Record<string, string | number | boolean | undefined>;
      json?: Record<string, unknown> | object;
      headers?: Record<string, string>;
      authRequired?: boolean;
    } = {},
  ): Promise<T> {
    const { params, json, headers: extraHeaders, authRequired = true } = options;

    if (authRequired) {
      await this.ensureToken();
    }

    const url = new URL(`${this.baseUrl}/api/${API_VERSION}${path}`);
    if (params) {
      for (const [key, value] of Object.entries(params)) {
        if (value !== undefined) url.searchParams.set(key, String(value));
      }
    }

    const headers: Record<string, string> = {
      'Accept': 'application/json',
      'User-Agent': `huntrecht-sdk-js/0.1.0`,
    };
    if (authRequired && this._accessToken) {
      headers['Authorization'] = `Bearer ${this._accessToken}`;
    }
    if (json) {
      headers['Content-Type'] = 'application/json';
    }
    if (extraHeaders) {
      Object.assign(headers, extraHeaders);
    }

    const init: RequestInit = {
      method,
      headers,
      signal: AbortSignal.timeout(this.timeout),
    };
    if (json) {
      init.body = JSON.stringify(json);
    }

    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
      try {
        const response = await fetch(url.toString(), init);
        return await this.handleResponse<T>(response);
      } catch (err) {
        if (err instanceof RateLimitError) {
          lastError = err;
          if (attempt < this.maxRetries) {
            const wait = err.retryAfter > 0 ? err.retryAfter * 1000 : this.retryBackoff * Math.pow(2, attempt);
            await sleep(wait);
            continue;
          }
          throw err;
        }
        lastError = err instanceof Error ? err : new HuntrechtError(String(err));
        if (attempt < this.maxRetries) {
          await sleep(this.retryBackoff * Math.pow(2, attempt));
          continue;
        }
        throw lastError;
      }
    }

    throw lastError ?? new HuntrechtError('Request failed');
  }

  private async ensureToken(): Promise<void> {
    if (this._accessToken && Date.now() < this._tokenExpiresAt) return;

    if (this.clientId && this.clientSecret) {
      const tokens = await this.auth.token();
      this._accessToken = tokens.access_token;
      this._refreshToken = tokens.refresh_token ?? null;
      this._tokenExpiresAt = Date.now() + (tokens.expires_in - 60) * 1000;
    } else {
      throw new AuthenticationError(
        'No access token and no client credentials. ' +
        'Set HUNTRECHT_CLIENT_ID and HUNTRECHT_CLIENT_SECRET, ' +
        'or pass them to HuntrechtClient().'
      );
    }
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (response.status === 204) return {} as T;

    let data: unknown;
    try {
      data = await response.json();
    } catch {
      data = { raw: await response.text() };
    }

    if (!response.ok) {
      const body = data as Record<string, unknown> | undefined;
      const msg = (body?.error_description as string) ?? `HTTP ${response.status}`;

      switch (response.status) {
        case 401:
          this._accessToken = null;
          throw new AuthenticationError(msg, response.status, body);
        case 403:
          throw new PermissionError(msg, response.status, body);
        case 404:
          throw new NotFoundError(msg, response.status, body);
        case 422:
          throw new ValidationError(msg, response.status, body);
        case 429: {
          const retryAfter = parseInt(response.headers.get('Retry-After') ?? '60', 10);
          throw new RateLimitError(msg, retryAfter, response.status, body);
        }
        default:
          throw new HuntrechtError(msg, response.status, body);
      }
    }

    return data as T;
  }
}

// ---- Resource classes ----

class APIResource {
  constructor(protected readonly _client: HuntrechtClient) {}
  protected request<T = unknown>(method: string, path: string, options?: Parameters<HuntrechtClient['request']>[2]) {
    return this._client.request<T>(method, path, options);
  }
}

export class AuthAPI extends APIResource {
  async token(opts: {
    grantType?: string;
    clientId?: string;
    clientSecret?: string;
    refreshToken?: string;
    scope?: string;
  } = {}) {
    const { grantType = 'client_credentials', clientId, clientSecret, refreshToken, scope } = opts;
    const body: Record<string, string> = { grant_type: grantType };
    if (grantType === 'client_credentials') {
      body.client_id = clientId ?? this._client.clientId;
      body.client_secret = clientSecret ?? this._client.clientSecret;
      if (scope) body.scope = scope;
    } else if (grantType === 'refresh_token') {
      body.refresh_token = refreshToken ?? this._client._refreshToken ?? '';
    }
    const data = await this.request<{ access_token: string; token_type: string; expires_in: number; refresh_token?: string; scope: string }>('POST', '/auth/token', { json: body, authRequired: false });
    this._client._accessToken = data.access_token;
    this._client._refreshToken = data.refresh_token ?? null;
    return data as import('./types.js').TokenResponse;
  }

  async revoke(token?: string) {
    const tok = token ?? this._client._accessToken ?? '';
    return this.request<Record<string, unknown>>('POST', '/auth/revoke', { params: { token: tok }, authRequired: false });
  }
}

export class ClientsAPI extends APIResource {
  async list(userId: number) {
    return this.request<import('./types.js').ApiClientResponse[]>('GET', '/clients', { params: { user_id: userId } });
  }
  async create(userId: number, data: import('./types.js').ApiClientCreate) {
    return this.request<import('./types.js').ApiClientWithSecret>('POST', '/clients', { params: { user_id: userId }, json: data });
  }
  async update(userId: number, clientId: string, data: Partial<import('./types.js').ApiClientCreate>) {
    return this.request<import('./types.js').ApiClientResponse>('PATCH', `/clients/${clientId}`, { params: { user_id: userId }, json: data });
  }
  async rotateSecret(userId: number, clientId: string) {
    return this.request<import('./types.js').ApiClientRotateResponse>('POST', `/clients/${clientId}/rotate`, { params: { user_id: userId } });
  }
  async delete(userId: number, clientId: string) {
    return this.request<Record<string, string>>('DELETE', `/clients/${clientId}`, { params: { user_id: userId } });
  }
}

export class OrdersAPI extends APIResource {
  async list(opts: { page?: number; perPage?: number; status?: string } = {}) {
    const { page = 1, perPage = 20, status } = opts;
    const params: Record<string, string | number> = { page, per_page: perPage };
    if (status) params.status = status;
    return this.request<import('./types.js').OrderListResponse>('GET', '/orders', { params });
  }
  async get(orderId: string) {
    return this.request<{ data: import('./types.js').Order }>('GET', `/orders/${orderId}`);
  }
  async create(opts: { commodity: string; quantity: number; deliveryTerms?: string; destination?: string; currency?: string }) {
    const { commodity, quantity, deliveryTerms = 'FOB', destination, currency = 'USD' } = opts;
    const params: Record<string, string | number> = { commodity, quantity, delivery_terms: deliveryTerms, currency };
    if (destination) params.destination = destination;
    return this.request<{ data: import('./types.js').Order; message: string }>('POST', '/orders', { params });
  }
}

export class PaymentsAPI extends APIResource {
  async list(opts: { page?: number; perPage?: number; status?: string } = {}) {
    const { page = 1, perPage = 20, status } = opts;
    const params: Record<string, string | number> = { page, per_page: perPage };
    if (status) params.status = status;
    return this.request<import('./types.js').PaymentListResponse>('GET', '/payments', { params });
  }
  async get(paymentId: string) {
    return this.request<{ data: import('./types.js').Payment }>('GET', `/payments/${paymentId}`);
  }
  async create(data: import('./types.js').CreatePaymentRequest) {
    return this.request<{ data: import('./types.js').Payment; message: string }>('POST', '/payments', { json: data });
  }
}

export class SubscriptionsAPI extends APIResource {
  async list(opts: { page?: number; perPage?: number; status?: string; includePaymentHistory?: boolean } = {}) {
    const { page = 1, perPage = 20, status, includePaymentHistory = false } = opts;
    const params: Record<string, string | number | boolean> = { page, per_page: perPage, include_payment_history: includePaymentHistory };
    if (status) params.status = status;
    return this.request<import('./types.js').SubscriptionListResponse>('GET', '/subscriptions', { params });
  }
  async get(subscriptionId: string) {
    return this.request<{ data: import('./types.js').Subscription }>('GET', `/subscriptions/${subscriptionId}`);
  }
}

export class CreditAPI extends APIResource {
  async assess(data: import('./types.js').CreditAssessmentRequest) {
    return this.request<{ data: import('./types.js').CreditAssessmentData }>('POST', '/credit/assess', { json: data });
  }
  async score(customerEmail: string) {
    return this.request<{ data: import('./types.js').CreditScoreData }>('GET', `/credit/score/${customerEmail}`);
  }
}

export class KycAPI extends APIResource {
  async list(opts: { page?: number; perPage?: number; status?: string } = {}) {
    const { page = 1, perPage = 20, status } = opts;
    const params: Record<string, string | number> = { page, per_page: perPage };
    if (status) params.status = status;
    return this.request<import('./types.js').KycListResponse>('GET', '/kyc', { params });
  }
  async get(submissionId: string) {
    return this.request<{ data: import('./types.js').KycSubmission }>('GET', `/kyc/${submissionId}`);
  }
  async submit(data: import('./types.js').KycSubmitRequest) {
    return this.request<{ data: import('./types.js').KycSubmission; message: string }>('POST', '/kyc', { json: data });
  }
}

export class QuotesAPI extends APIResource {
  async list(opts: { page?: number; perPage?: number } = {}) {
    const { page = 1, perPage = 20 } = opts;
    return this.request<import('./types.js').QuoteListResponse>('GET', '/quotes', { params: { page, per_page: perPage } });
  }
  async get(quoteId: string) {
    return this.request<{ data: import('./types.js').CommodityQuote }>('GET', `/quotes/${quoteId}`);
  }
  async create(data: import('./types.js').QuoteRequest) {
    return this.request<{ data: import('./types.js').CommodityQuote; message: string }>('POST', '/quotes', { json: data });
  }
}

export class UsersAPI extends APIResource {
  async me() {
    return this.request<{ data: import('./types.js').UserProfile }>('GET', '/users/me');
  }
  async get(userId: string) {
    return this.request<{ data: import('./types.js').UserProfile }>('GET', `/users/${userId}`);
  }
}

export class StorefrontAPI extends APIResource {
  async collections(opts: { first?: number; includeProducts?: boolean } = {}) {
    const { first = 20, includeProducts = false } = opts;
    return this.request<{ data: import('./types.js').CollectionResponse[]; cached: boolean }>('GET', '/storefront/collections', {
      params: { first: Math.min(first, 100), include_products: includeProducts },
    });
  }
  async collection(handle: string, opts: { productsFirst?: number } = {}) {
    const { productsFirst = 20 } = opts;
    return this.request<{ data: import('./types.js').CollectionWithProducts; cached: boolean }>('GET', `/storefront/collections/${handle}`, {
      params: { products_first: Math.min(productsFirst, 250) },
    });
  }
  async products(opts: { first?: number; after?: string; b2bOnly?: boolean } = {}) {
    const { first = 20, after, b2bOnly = false } = opts;
    const params: Record<string, string | number | boolean> = { first: Math.min(first, 100), b2b_only: b2bOnly };
    if (after) params.after = after;
    return this.request<{ data: import('./types.js').ProductResponse[]; pagination: import('./types.js').CursorPagination }>('GET', '/storefront/products', { params });
  }
  async product(handle: string) {
    return this.request<{ data: import('./types.js').ProductResponse; cached: boolean }>('GET', `/storefront/products/${handle}`);
  }
  async search(query: string, opts: { first?: number; b2bOnly?: boolean } = {}) {
    const { first = 10, b2bOnly = false } = opts;
    return this.request<{ data: import('./types.js').ProductResponse[]; query: string; count: number }>('GET', '/storefront/search', {
      params: { query, first: Math.min(first, 50), b2b_only: b2bOnly },
    });
  }
}

export class PriceDropsAPI extends APIResource {
  async list(opts: { limit?: number; minDiscount?: number; days?: number } = {}) {
    const { limit = 10, minDiscount = 5.0, days = 7 } = opts;
    return this.request<import('./types.js').PriceDropListResponse>('GET', '/price-drops', {
      params: { limit: Math.min(limit, 50), min_discount: minDiscount, days },
      authRequired: false,
    });
  }
  async featured(opts: { limit?: number } = {}) {
    const { limit = 10 } = opts;
    return this.request<{ data: import('./types.js').PriceDropEvent[]; count: number; headline: string }>('GET', '/price-drops/featured', {
      params: { limit: Math.min(limit, 10) },
      authRequired: false,
    });
  }
}

export class AppProxyAPI extends APIResource {
  async collections(opts: { first?: number; signature?: string } = {}) {
    const { first = 20, signature } = opts;
    const params: Record<string, string | number> = { first: Math.min(first, 100) };
    if (signature) params.signature = signature;
    return this.request<Record<string, unknown>>('GET', '/app-proxy/collections', { params, authRequired: false });
  }
  async collection(handle: string, opts: { first?: number; signature?: string } = {}) {
    const { first = 20, signature } = opts;
    const params: Record<string, string | number> = { first: Math.min(first, 250) };
    if (signature) params.signature = signature;
    return this.request<Record<string, unknown>>('GET', `/app-proxy/collections/${handle}`, { params, authRequired: false });
  }
  async priceDrops(opts: { limit?: number; minDiscount?: number } = {}) {
    const { limit = 10, minDiscount = 5.0 } = opts;
    return this.request<Record<string, unknown>>('GET', '/app-proxy/price-drops', {
      params: { limit: Math.min(limit, 20), min_discount: minDiscount },
      authRequired: false,
    });
  }
  async paymentMethods(opts: { customerId?: string; productPrice?: number; b2bExclusive?: boolean; signature?: string } = {}) {
    const { customerId, productPrice = 0, b2bExclusive = false, signature } = opts;
    const params: Record<string, string | number | boolean> = { product_price: productPrice, b2b_exclusive: b2bExclusive };
    if (customerId) params.customer_id = customerId;
    if (signature) params.signature = signature;
    return this.request<Record<string, unknown>>('GET', '/app-proxy/payment-methods', { params, authRequired: false });
  }
}

export class LinkedPaymentsAPI extends APIResource {
  async checkEligibility(customerId: string, opts: { productPrice?: number; b2bExclusive?: boolean } = {}) {
    const { productPrice = 0, b2bExclusive = false } = opts;
    return this.request<import('./types.js').PaymentEligibilityResponse>('GET', '/linked-payments/check-eligibility', {
      params: { customer_id: customerId, product_price: productPrice, b2b_exclusive: b2bExclusive },
      authRequired: false,
    });
  }
  async linkWallet(data: import('./types.js').LinkedWalletRequest) {
    return this.request<{ success: boolean; wallet: import('./types.js').LinkedWallet; message: string }>('POST', '/linked-payments/link-wallet', { json: data });
  }
  async linkBank(data: import('./types.js').LinkedBankRequest) {
    return this.request<{ success: boolean; bank: import('./types.js').LinkedBank; message: string }>('POST', '/linked-payments/link-bank', { json: data });
  }
  async linkedAccounts(customerId: string) {
    return this.request<import('./types.js').LinkedAccountsResponse>('GET', `/linked-payments/linked-accounts/${customerId}`);
  }
}

// ---- Helpers ----

function createResources(client: HuntrechtClient) {
  return {
    auth: new AuthAPI(client),
    clients: new ClientsAPI(client),
    orders: new OrdersAPI(client),
    payments: new PaymentsAPI(client),
    subscriptions: new SubscriptionsAPI(client),
    credit: new CreditAPI(client),
    kyc: new KycAPI(client),
    quotes: new QuotesAPI(client),
    users: new UsersAPI(client),
    storefront: new StorefrontAPI(client),
    priceDrops: new PriceDropsAPI(client),
    appProxy: new AppProxyAPI(client),
    linkedPayments: new LinkedPaymentsAPI(client),
  };
}

function processEnv(key: string): string | undefined {
  try {
    return typeof process !== 'undefined' ? process.env?.[key] : undefined;
  } catch {
    return undefined;
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}
