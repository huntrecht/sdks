// Package huntrecht provides a Go client for the Huntrecht Platform API v1.
package huntrecht

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"time"
)

const (
	defaultBaseURL = "https://api.huntrecht.com"
	apiVersion     = "v1"
	userAgent      = "huntrecht-sdk-go/0.1.0"
)

// Client is the Huntrecht Platform API client.
type Client struct {
	BaseURL      string
	ClientID     string
	ClientSecret string
	HTTPClient   *http.Client

	accessToken  string
	refreshToken string
	tokenExpiry  time.Time

	Auth           *AuthService
	Clients        *ClientsService
	Orders         *OrdersService
	Payments       *PaymentsService
	Subscriptions  *SubscriptionsService
	Credit         *CreditService
	KYC            *KYCService
	Quotes         *QuotesService
	Users          *UsersService
	Storefront     *StorefrontService
	PriceDrops     *PriceDropsService
	LinkedPayments *LinkedPaymentsService
}

// NewClient creates a new Huntrecht API client.
func NewClient(opts ...Option) *Client {
	c := &Client{
		BaseURL:    envOr("HUNTRECHT_BASE_URL", defaultBaseURL),
		ClientID:   envOr("HUNTRECHT_CLIENT_ID", ""),
		HTTPClient: &http.Client{Timeout: 30 * time.Second},
	}
	for _, opt := range opts {
		opt(c)
	}
	c.ClientSecret = envOr("HUNTRECHT_CLIENT_SECRET", c.ClientSecret)

	c.Auth = &AuthService{client: c}
	c.Clients = &ClientsService{client: c}
	c.Orders = &OrdersService{client: c}
	c.Payments = &PaymentsService{client: c}
	c.Subscriptions = &SubscriptionsService{client: c}
	c.Credit = &CreditService{client: c}
	c.KYC = &KYCService{client: c}
	c.Quotes = &QuotesService{client: c}
	c.Users = &UsersService{client: c}
	c.Storefront = &StorefrontService{client: c}
	c.PriceDrops = &PriceDropsService{client: c}
	c.LinkedPayments = &LinkedPaymentsService{client: c}

	return c
}

// Option configures a Client.
type Option func(*Client)

// WithClientID sets the OAuth2 client ID.
func WithClientID(id string) Option { return func(c *Client) { c.ClientID = id } }

// WithClientSecret sets the OAuth2 client secret.
func WithClientSecret(secret string) Option { return func(c *Client) { c.ClientSecret = secret } }

// WithBaseURL sets the API base URL.
func WithBaseURL(u string) Option { return func(c *Client) { c.BaseURL = u } }

// WithHTTPClient sets the HTTP client.
func WithHTTPClient(hc *http.Client) Option { return func(c *Client) { c.HTTPClient = hc } }

func (c *Client) ensureToken(ctx context.Context) error {
	if c.accessToken != "" && time.Now().Before(c.tokenExpiry) {
		return nil
	}
	if c.ClientID == "" || c.ClientSecret == "" {
		return fmt.Errorf("no access token and no client credentials")
	}
	tokens, err := c.Auth.Token(ctx, c.ClientID, c.ClientSecret)
	if err != nil {
		return err
	}
	c.accessToken = tokens.AccessToken
	c.refreshToken = tokens.RefreshToken
	c.tokenExpiry = time.Now().Add(time.Duration(tokens.ExpiresIn-60) * time.Second)
	return nil
}

func (c *Client) do(ctx context.Context, method, path string, params url.Values, body, result interface{}, authRequired bool) error {
	if authRequired {
		if err := c.ensureToken(ctx); err != nil {
			return err
		}
	}

	u := fmt.Sprintf("%s/api/%s%s", c.BaseURL, apiVersion, path)
	if params != nil {
		u += "?" + params.Encode()
	}

	var reqBody io.Reader
	if body != nil {
		data, err := json.Marshal(body)
		if err != nil {
			return err
		}
		reqBody = bytes.NewReader(data)
	}

	req, err := http.NewRequestWithContext(ctx, method, u, reqBody)
	if err != nil {
		return err
	}
	req.Header.Set("Accept", "application/json")
	req.Header.Set("User-Agent", userAgent)
	if authRequired && c.accessToken != "" {
		req.Header.Set("Authorization", "Bearer "+c.accessToken)
	}
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}

	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	return handleResponse(resp, result)
}

func handleResponse(resp *http.Response, result interface{}) error {
	if resp.StatusCode == 204 {
		return nil
	}
	data, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("read body: %w", err)
	}
	if resp.StatusCode >= 400 {
		var apiErr struct {
			Error            string `json:"error"`
			ErrorDescription string `json:"error_description"`
		}
		_ = json.Unmarshal(data, &apiErr)
		msg := apiErr.ErrorDescription
		if msg == "" {
			msg = fmt.Sprintf("HTTP %d", resp.StatusCode)
		}
		return &APIError{Message: msg, StatusCode: resp.StatusCode}
	}
	if result != nil {
		return json.Unmarshal(data, result)
	}
	return nil
}

// APIError represents an error from the API.
type APIError struct {
	Message    string
	StatusCode int
}

func (e *APIError) Error() string { return e.Message }

func envOr(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
