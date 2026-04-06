/** All v1 API types matching Platform API response schemas. */

export interface Pagination {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface CursorPagination {
  has_next: boolean;
  end_cursor: string;
}

// Auth
export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token?: string;
  scope: string;
}

// API Clients
export interface ApiClientCreate {
  client_name: string;
  description?: string;
  webhook_url?: string;
  ip_allowlist?: string[];
  scopes?: string[];
}

export interface ApiClientResponse {
  id: number;
  client_id: string;
  client_name: string;
  description?: string;
  status: string;
  scopes: string[];
  ip_allowlist: string[];
  webhook_url?: string;
  created_at: string;
  last_used_at?: string;
}

export interface ApiClientWithSecret extends ApiClientResponse {
  client_secret: string;
}

export interface ApiClientRotateResponse {
  client_id: string;
  client_secret: string;
  message: string;
}

// Users
export interface UserProfile {
  id: number;
  email: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
  role: string;
  permissions: string[];
  company_name?: string;
  subscription_plan: string;
  email_verified: boolean;
  created_at: string;
}

// Orders
export interface Order {
  id: string;
  user_id: string;
  commodity: string;
  quantity: number;
  delivery_terms: string;
  destination?: string;
  currency: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface OrderAggregate {
  total_orders: number;
  pending: number;
  confirmed: number;
  fulfilled: number;
  cancelled: number;
}

export interface OrderListResponse {
  data: Order[];
  pagination: Pagination;
  aggregates?: OrderAggregate;
}

// Payments
export interface Payment {
  id: string;
  user_id: string;
  subscription_id: number;
  amount: number;
  currency: string;
  payment_method: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface PaymentListResponse {
  data: Payment[];
  pagination: Pagination;
}

export interface CreatePaymentRequest {
  subscription_id: number;
  amount: number;
  currency?: string;
  payment_method?: string;
}

// Subscriptions
export interface PaymentHistoryItem {
  id: string;
  amount: number;
  status: string;
  paid_at: string;
}

export interface Subscription {
  id: string;
  user_id: string;
  plan: string;
  status: string;
  amount: number;
  currency: string;
  billing_cycle: string;
  start_date: string;
  end_date?: string;
  payment_history: PaymentHistoryItem[];
  created_at: string;
  updated_at: string;
}

export interface SubscriptionListResponse {
  data: Subscription[];
  pagination: Pagination;
}

// Credit
export interface CreditScoreData {
  credit_score: number;
  risk_level: string;
  fico_equivalent?: number;
}

export interface CreditAssessmentData {
  credit_score: number;
  risk_level: string;
  factors: string[];
  recommendations: string[];
  assessed_at: string;
}

export interface CreditAssessmentRequest {
  customer_email: string;
  include_recommendations?: boolean;
}

// KYC
export interface KycSubmission {
  id: string;
  user_id: string;
  company_name: string;
  company_type: string;
  registration_number?: string;
  address?: string;
  contact_info?: string;
  status: string;
  submitted_at: string;
  reviewed_at?: string;
}

export interface KycListResponse {
  data: KycSubmission[];
  pagination: Pagination;
}

export interface KycSubmitRequest {
  company_name: string;
  company_type: string;
  registration_number?: string;
  address?: Record<string, string>;
  contact_info?: Record<string, string>;
}

// Quotes
export interface CommodityQuote {
  id: string;
  user_id: string;
  commodity: string;
  quantity: number;
  unit: string;
  delivery_location?: string;
  price: number;
  currency: string;
  status: string;
  valid_until: string;
  created_at: string;
}

export interface QuoteListResponse {
  data: CommodityQuote[];
  pagination: Pagination;
}

export interface QuoteRequest {
  commodity: string;
  quantity: number;
  unit?: string;
  delivery_location?: string;
}

// Storefront
export interface CollectionResponse {
  id: string;
  title: string;
  handle: string;
  description?: string;
  image_url?: string;
  image_alt?: string;
}

export interface ProductResponse {
  id: string;
  title: string;
  handle: string;
  description?: string;
  price: number;
  currency: string;
  image_url?: string;
  available: boolean;
  b2b_exclusive: boolean;
  compare_at_price?: number;
}

export interface CollectionWithProducts {
  collection: CollectionResponse;
  products: ProductResponse[];
}

// Price Drops
export interface PriceDropEvent {
  product_id: string;
  product_title: string;
  product_handle: string;
  old_price: number;
  new_price: number;
  currency: string;
  image_url?: string;
  vendor?: string;
  discount_percentage: number;
}

export interface PriceDropListResponse {
  data: PriceDropEvent[];
  count: number;
}

// Linked Payments
export interface PaymentEligibilityResponse {
  eligible: boolean;
  has_customer_role: boolean;
  is_b2b_product: boolean;
  available_methods: string[];
  message: string;
}

export interface LinkedWalletRequest {
  customer_id: string;
  wallet_address?: string;
  wallet_provider?: string;
}

export interface LinkedBankRequest {
  customer_id: string;
  plaid_access_token?: string;
  account_id?: string;
}

export interface LinkedWallet {
  id: string;
  customer_id: string;
  wallet_address: string;
  wallet_provider: string;
  created_at: string;
}

export interface LinkedBank {
  id: string;
  customer_id: string;
  bank_name: string;
  account_masked: string;
  created_at: string;
}

export interface LinkedAccountsResponse {
  wallets: LinkedWallet[];
  banks: LinkedBank[];
  has_linked_payments: boolean;
}
