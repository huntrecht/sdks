/**
 * Huntrecht Platform SDK for TypeScript/JavaScript
 *
 * Official client for the Huntrecht Platform API v1.
 * Works in Node.js (18+) and modern browsers.
 *
 * @example
 * ```ts
 * import { HuntrechtClient } from '@huntrecht/sdk';
 *
 * const client = new HuntrechtClient({
 *   clientId: 'hnt_your_client_id',
 *   clientSecret: 'your_secret',
 * });
 *
 * await client.auth.token();
 * const orders = await client.orders.list();
 * ```
 */

export { HuntrechtClient, type HuntrechtClientOptions } from './client.js';
export {
  HuntrechtError,
  AuthenticationError,
  RateLimitError,
  NotFoundError,
  ValidationError,
  PermissionError,
} from './errors.js';

export type {
  // Auth
  TokenResponse,
  // Clients
  ApiClientCreate,
  ApiClientResponse,
  ApiClientWithSecret,
  ApiClientRotateResponse,
  // Users
  UserProfile,
  // Orders
  Order,
  OrderAggregate,
  OrderListResponse,
  // Payments
  Payment,
  PaymentListResponse,
  CreatePaymentRequest,
  // Subscriptions
  Subscription,
  SubscriptionListResponse,
  PaymentHistoryItem,
  // Credit
  CreditScoreData,
  CreditAssessmentData,
  CreditAssessmentRequest,
  // KYC
  KycSubmission,
  KycListResponse,
  KycSubmitRequest,
  // Quotes
  CommodityQuote,
  QuoteListResponse,
  QuoteRequest,
  // Storefront
  CollectionResponse,
  ProductResponse,
  CollectionWithProducts,
  // Price Drops
  PriceDropEvent,
  PriceDropListResponse,
  // Linked Payments
  PaymentEligibilityResponse,
  LinkedWalletRequest,
  LinkedBankRequest,
  LinkedWallet,
  LinkedBank,
  LinkedAccountsResponse,
  // Common
  Pagination,
  CursorPagination,
} from './types.js';

export type {
  AuthAPI,
  ClientsAPI,
  OrdersAPI,
  PaymentsAPI,
  SubscriptionsAPI,
  CreditAPI,
  KycAPI,
  QuotesAPI,
  UsersAPI,
  StorefrontAPI,
  PriceDropsAPI,
  AppProxyAPI,
  LinkedPaymentsAPI,
} from './client.js';
