// Service resources for the Huntrecht Platform API v1.
//
// Every method mirrors the Python/TypeScript SDK surface: same paths,
// same query parameters, same JSON bodies. Results decode into
// map[string]any unless a narrower type is declared.
package huntrecht

import (
	"context"
	"fmt"
	"net/url"
	"strconv"
)

type result = map[string]any

func values(pairs ...any) url.Values {
	v := url.Values{}
	for i := 0; i+1 < len(pairs); i += 2 {
		k, isStr := pairs[i].(string)
		if !isStr {
			continue
		}
		switch val := pairs[i+1].(type) {
		case nil:
		case string:
			if val != "" {
				v.Set(k, val)
			}
		case int:
			v.Set(k, strconv.Itoa(val))
		case int64:
			v.Set(k, strconv.FormatInt(val, 10))
		case bool:
			v.Set(k, strconv.FormatBool(val))
		case float64:
			v.Set(k, strconv.FormatFloat(val, 'f', -1, 64))
		default:
			v.Set(k, fmt.Sprint(val))
		}
	}
	return v
}

// Tokens mirrors the OAuth2 token response.
type Tokens struct {
	AccessToken  string `json:"access_token"`
	TokenType    string `json:"token_type"`
	ExpiresIn    int    `json:"expires_in"`
	RefreshToken string `json:"refresh_token"`
	Scope        string `json:"scope"`
}

// AuthService handles OAuth2 token lifecycle.
type AuthService struct{ client *Client }

// Token exchanges client credentials (or a refresh token) for tokens.
func (s *AuthService) Token(ctx context.Context, clientID, clientSecret string) (*Tokens, error) {
	return s.TokenWithOptions(ctx, clientID, clientSecret, "", "")
}

// TokenWithOptions supports grant_type, scope, and refresh flows.
func (s *AuthService) TokenWithOptions(ctx context.Context, clientID, clientSecret, refreshToken, scope string) (*Tokens, error) {
	body := map[string]any{"grant_type": "client_credentials"}
	if refreshToken != "" {
		body = map[string]any{"grant_type": "refresh_token", "refresh_token": refreshToken}
	} else {
		body["client_id"] = clientID
		body["client_secret"] = clientSecret
		if scope != "" {
			body["scope"] = scope
		}
	}
	var out Tokens
	if err := s.client.do(ctx, "POST", "/auth/token", nil, body, &out, false); err != nil {
		return nil, err
	}
	return &out, nil
}

// Revoke invalidates a token.
func (s *AuthService) Revoke(ctx context.Context, token string) (result, error) {
	var out result
	err := s.client.do(ctx, "POST", "/auth/revoke", values("token", token), nil, &out, false)
	return out, err
}

// ClientsService manages OAuth2 API clients.
type ClientsService struct{ client *Client }

// List returns API clients for a user.
func (s *ClientsService) List(ctx context.Context, userID int64) (result, error) {
	var out result
	err := s.client.do(ctx, "GET", "/clients", values("user_id", userID), nil, &out, true)
	return out, err
}

// Create registers a new API client; the secret is returned only once.
func (s *ClientsService) Create(ctx context.Context, userID int64, body map[string]any) (result, error) {
	var out result
	err := s.client.do(ctx, "POST", "/clients", values("user_id", userID), body, &out, true)
	return out, err
}

// RotateSecret rotates an API client's secret.
func (s *ClientsService) RotateSecret(ctx context.Context, userID int64, clientID string) (result, error) {
	var out result
	err := s.client.do(ctx, "POST", "/clients/"+clientID+"/rotate", values("user_id", userID), nil, &out, true)
	return out, err
}

// Delete removes an API client.
func (s *ClientsService) Delete(ctx context.Context, userID int64, clientID string) (result, error) {
	var out result
	err := s.client.do(ctx, "DELETE", "/clients/"+clientID, values("user_id", userID), nil, &out, true)
	return out, err
}

// OrdersService handles B2B orders.
type OrdersService struct{ client *Client }

// List returns paginated orders.
func (s *OrdersService) List(ctx context.Context, page, perPage int, status string) (result, error) {
	var out result
	err := s.client.do(ctx, "GET", "/orders", values("page", page, "per_page", perPage, "status", status), nil, &out, true)
	return out, err
}

// Get returns one order.
func (s *OrdersService) Get(ctx context.Context, orderID string) (result, error) {
	var out result
	err := s.client.do(ctx, "GET", "/orders/"+orderID, nil, nil, &out, true)
	return out, err
}

// Create places a new order.
func (s *OrdersService) Create(ctx context.Context, params map[string]string, body map[string]any) (result, error) {
	v := url.Values{}
	for k, val := range params {
		if val != "" {
			v.Set(k, val)
		}
	}
	var out result
	err := s.client.do(ctx, "POST", "/orders", v, body, &out, true)
	return out, err
}

// PaymentsService handles payments.
type PaymentsService struct{ client *Client }

// List returns paginated payments.
func (s *PaymentsService) List(ctx context.Context, page, perPage int, status string) (result, error) {
	var out result
	err := s.client.do(ctx, "GET", "/payments", values("page", page, "per_page", perPage, "status", status), nil, &out, true)
	return out, err
}

// Get returns one payment.
func (s *PaymentsService) Get(ctx context.Context, paymentID string) (result, error) {
	var out result
	err := s.client.do(ctx, "GET", "/payments/"+paymentID, nil, nil, &out, true)
	return out, err
}

// Create records a new payment.
func (s *PaymentsService) Create(ctx context.Context, body map[string]any) (result, error) {
	var out result
	err := s.client.do(ctx, "POST", "/payments", nil, body, &out, true)
	return out, err
}

// SubscriptionsService manages B2B subscriptions.
type SubscriptionsService struct{ client *Client }

// List returns paginated subscriptions.
func (s *SubscriptionsService) List(ctx context.Context, page, perPage int, status string, includeHistory bool) (result, error) {
	var out result
	err := s.client.do(ctx, "GET", "/subscriptions", values("page", page, "per_page", perPage, "status", status, "include_payment_history", includeHistory), nil, &out, true)
	return out, err
}

// Get returns one subscription.
func (s *SubscriptionsService) Get(ctx context.Context, subscriptionID string) (result, error) {
	var out result
	err := s.client.do(ctx, "GET", "/subscriptions/"+subscriptionID, nil, nil, &out, true)
	return out, err
}

// CreditService runs basic credit scoring.
type CreditService struct{ client *Client }

// Assess runs a credit assessment.
func (s *CreditService) Assess(ctx context.Context, body map[string]any) (result, error) {
	var out result
	err := s.client.do(ctx, "POST", "/credit/assess", nil, body, &out, true)
	return out, err
}

// Score returns the credit score for a customer email.
func (s *CreditService) Score(ctx context.Context, customerEmail string) (result, error) {
	var out result
	err := s.client.do(ctx, "GET", "/credit/score/"+customerEmail, nil, nil, &out, true)
	return out, err
}

// CreditRiskService covers risk scoring, company assessments, improvement,
// and connected credit-history reads.
type CreditRiskService struct{ client *Client }

// GetScore returns the risk score for a customer.
func (s *CreditRiskService) GetScore(ctx context.Context, customerID string) (result, error) {
	var out result
	err := s.client.do(ctx, "GET", "/credit-risk/score", values("customer_id", customerID), nil, &out, true)
	return out, err
}

// Assess requests a risk assessment.
func (s *CreditRiskService) Assess(ctx context.Context, body map[string]any) (result, error) {
	var out result
	err := s.client.do(ctx, "POST", "/credit-risk/assess", nil, body, &out, true)
	return out, err
}

// GetHistory reads connected credit history.
func (s *CreditRiskService) GetHistory(ctx context.Context, customerID string, limit int) (result, error) {
	var out result
	err := s.client.do(ctx, "GET", "/data-connect/credit-history", values("customer_id", customerID, "limit", limit), nil, &out, true)
	return out, err
}

// GetAssessment returns a company's credit assessment.
func (s *CreditRiskService) GetAssessment(ctx context.Context, userID string) (result, error) {
	var out result
	err := s.client.do(ctx, "GET", "/company/credit-assessment", values("user_id", userID), nil, &out, true)
	return out, err
}

// RequestAssessment opens a new company assessment.
func (s *CreditRiskService) RequestAssessment(ctx context.Context, body map[string]any) (result, error) {
	var out result
	err := s.client.do(ctx, "POST", "/company/credit-assessment/request", nil, body, &out, true)
	return out, err
}

// GetImprovementOptions lists credit-improvement options.
func (s *CreditRiskService) GetImprovementOptions(ctx context.Context) (result, error) {
	var out result
	err := s.client.do(ctx, "GET", "/credit-improvement/available-options", nil, nil, &out, true)
	return out, err
}

// ConnectWallet links a wallet for credit improvement.
func (s *CreditRiskService) ConnectWallet(ctx context.Context, body map[string]any) (result, error) {
	var out result
	err := s.client.do(ctx, "POST", "/credit-improvement/connect-wallet", nil, body, &out, true)
	return out, err
}

// ApplyBoosts applies credit-improvement boosts.
func (s *CreditRiskService) ApplyBoosts(ctx context.Context, body map[string]any) (result, error) {
	var out result
	err := s.client.do(ctx, "POST", "/credit-improvement/apply-boosts", nil, body, &out, true)
	return out, err
}

// KYCService handles KYC submissions.
type KYCService struct{ client *Client }

// List returns paginated KYC submissions.
func (s *KYCService) List(ctx context.Context, page, perPage int, status string) (result, error) {
	var out result
	err := s.client.do(ctx, "GET", "/kyc", values("page", page, "per_page", perPage, "status", status), nil, &out, true)
	return out, err
}

// Get returns one submission.
func (s *KYCService) Get(ctx context.Context, submissionID string) (result, error) {
	var out result
	err := s.client.do(ctx, "GET", "/kyc/"+submissionID, nil, nil, &out, true)
	return out, err
}

// Submit files a new KYC submission.
func (s *KYCService) Submit(ctx context.Context, body map[string]any) (result, error) {
	var out result
	err := s.client.do(ctx, "POST", "/kyc", nil, body, &out, true)
	return out, err
}

// QuotesService handles commodity quotes.
type QuotesService struct{ client *Client }

// Get returns one quote.
func (s *QuotesService) Get(ctx context.Context, quoteID string) (result, error) {
	var out result
	err := s.client.do(ctx, "GET", "/quotes/"+quoteID, nil, nil, &out, true)
	return out, err
}

// Create requests a new quote.
func (s *QuotesService) Create(ctx context.Context, body map[string]any) (result, error) {
	var out result
	err := s.client.do(ctx, "POST", "/quotes", nil, body, &out, true)
	return out, err
}

// UsersService reads user profiles.
type UsersService struct{ client *Client }

// Me returns the calling user.
func (s *UsersService) Me(ctx context.Context) (result, error) {
	var out result
	err := s.client.do(ctx, "GET", "/users/me", nil, nil, &out, true)
	return out, err
}

// Get returns one user.
func (s *UsersService) Get(ctx context.Context, userID string) (result, error) {
	var out result
	err := s.client.do(ctx, "GET", "/users/"+userID, nil, nil, &out, true)
	return out, err
}

// StorefrontService reads the Shopify-backed catalog.
type StorefrontService struct{ client *Client }

// Collections lists collections.
func (s *StorefrontService) Collections(ctx context.Context, first int, includeProducts bool) (result, error) {
	var out result
	err := s.client.do(ctx, "GET", "/storefront/collections", values("first", first, "include_products", includeProducts), nil, &out, true)
	return out, err
}

// Collection returns one collection with products.
func (s *StorefrontService) Collection(ctx context.Context, handle string, productsFirst int) (result, error) {
	var out result
	err := s.client.do(ctx, "GET", "/storefront/collections/"+handle, values("products_first", productsFirst), nil, &out, true)
	return out, err
}

// Products lists products.
func (s *StorefrontService) Products(ctx context.Context, first int, after string, b2bOnly bool) (result, error) {
	var out result
	err := s.client.do(ctx, "GET", "/storefront/products", values("first", first, "after", after, "b2b_only", b2bOnly), nil, &out, true)
	return out, err
}

// Product returns one product.
func (s *StorefrontService) Product(ctx context.Context, handle string) (result, error) {
	var out result
	err := s.client.do(ctx, "GET", "/storefront/products/"+handle, nil, nil, &out, true)
	return out, err
}

// Search queries the catalog.
func (s *StorefrontService) Search(ctx context.Context, query string, first int, b2bOnly bool) (result, error) {
	var out result
	err := s.client.do(ctx, "GET", "/storefront/search", values("query", query, "first", first, "b2b_only", b2bOnly), nil, &out, true)
	return out, err
}

// PriceDropsService reads price-drop events (public).
type PriceDropsService struct{ client *Client }

// List returns recent price drops.
func (s *PriceDropsService) List(ctx context.Context, limit int, minDiscount float64, days int) (result, error) {
	var out result
	err := s.client.do(ctx, "GET", "/price-drops", values("limit", limit, "min_discount", minDiscount, "days", days), nil, &out, false)
	return out, err
}

// Featured returns headline drops.
func (s *PriceDropsService) Featured(ctx context.Context, limit int) (result, error) {
	var out result
	err := s.client.do(ctx, "GET", "/price-drops/featured", values("limit", limit), nil, &out, false)
	return out, err
}

// AppProxyService calls theme-safe proxy endpoints (public).
type AppProxyService struct{ client *Client }

// Collections lists collections via the app proxy.
func (s *AppProxyService) Collections(ctx context.Context, first int, signature string) (result, error) {
	var out result
	err := s.client.do(ctx, "GET", "/app-proxy/collections", values("first", first, "signature", signature), nil, &out, false)
	return out, err
}

// Collection returns one proxied collection.
func (s *AppProxyService) Collection(ctx context.Context, handle string, first int, signature string) (result, error) {
	var out result
	err := s.client.do(ctx, "GET", "/app-proxy/collections/"+handle, values("first", first, "signature", signature), nil, &out, false)
	return out, err
}

// PriceDrops returns proxied drops.
func (s *AppProxyService) PriceDrops(ctx context.Context, limit int, minDiscount float64) (result, error) {
	var out result
	err := s.client.do(ctx, "GET", "/app-proxy/price-drops", values("limit", limit, "min_discount", minDiscount), nil, &out, false)
	return out, err
}

// PaymentMethods returns eligible B2B payment methods.
func (s *AppProxyService) PaymentMethods(ctx context.Context, customerID string, productPrice float64, b2bExclusive bool, signature string) (result, error) {
	var out result
	err := s.client.do(ctx, "GET", "/app-proxy/payment-methods", values("customer_id", customerID, "product_price", productPrice, "b2b_exclusive", b2bExclusive, "signature", signature), nil, &out, false)
	return out, err
}

// LinkedPaymentsService manages linked wallets and bank accounts.
type LinkedPaymentsService struct{ client *Client }

// CheckEligibility checks payment-method eligibility (public).
func (s *LinkedPaymentsService) CheckEligibility(ctx context.Context, customerID string, productPrice float64, b2bExclusive bool) (result, error) {
	var out result
	err := s.client.do(ctx, "GET", "/linked-payments/check-eligibility", values("customer_id", customerID, "product_price", productPrice, "b2b_exclusive", b2bExclusive), nil, &out, false)
	return out, err
}

// LinkWallet links a crypto wallet.
func (s *LinkedPaymentsService) LinkWallet(ctx context.Context, body map[string]any) (result, error) {
	var out result
	err := s.client.do(ctx, "POST", "/linked-payments/link-wallet", nil, body, &out, true)
	return out, err
}

// LinkBank links a bank account via Plaid.
func (s *LinkedPaymentsService) LinkBank(ctx context.Context, body map[string]any) (result, error) {
	var out result
	err := s.client.do(ctx, "POST", "/linked-payments/link-bank", nil, body, &out, true)
	return out, err
}

// LinkedAccounts lists a customer's linked accounts.
func (s *LinkedPaymentsService) LinkedAccounts(ctx context.Context, customerID string) (result, error) {
	var out result
	err := s.client.do(ctx, "GET", "/linked-payments/linked-accounts/"+customerID, nil, nil, &out, true)
	return out, err
}
