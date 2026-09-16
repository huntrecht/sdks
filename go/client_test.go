package huntrecht

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

func testServer(t *testing.T, _seen *string) *httptest.Server {
	t.Helper()
	return httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		*_seen = r.Method + " " + r.URL.Path
		if r.Header.Get("User-Agent") != userAgent {
			t.Errorf("User-Agent = %q, want %q", r.Header.Get("User-Agent"), userAgent)
		}
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]any{"ok": true})
	}))
}

func testClient(srv *httptest.Server) *Client {
	return NewClient(
		WithBaseURL(srv.URL),
		WithHTTPClient(srv.Client()),
		WithClientID("id"),
		WithClientSecret("secret"),
	)
}

// withToken presets a fresh token so ensureToken never hits the network.
func withToken(c *Client) {
	c.accessToken = "tok"
	c.tokenExpiry = time.Now().Add(time.Hour)
}

func TestCreditRiskPaths(t *testing.T) {
	var seen string
	srv := testServer(t, &seen)
	defer srv.Close()
	c := testClient(srv)
	withToken(c)
	ctx := context.Background()

	cases := []struct {
		name string
		call func() error
		want string
	}{
		{"score", func() error { _, err := c.CreditRisk.GetScore(ctx, "c1"); return err }, "GET /api/v1/credit-risk/score"},
		{"assess", func() error { _, err := c.CreditRisk.Assess(ctx, map[string]any{}); return err }, "POST /api/v1/credit-risk/assess"},
		{"history", func() error { _, err := c.CreditRisk.GetHistory(ctx, "c1", 5); return err }, "GET /api/v1/data-connect/credit-history"},
		{"company", func() error { _, err := c.CreditRisk.GetAssessment(ctx, "u1"); return err }, "GET /api/v1/company/credit-assessment"},
		{"request", func() error { _, err := c.CreditRisk.RequestAssessment(ctx, map[string]any{}); return err }, "POST /api/v1/company/credit-assessment/request"},
		{"options", func() error { _, err := c.CreditRisk.GetImprovementOptions(ctx); return err }, "GET /api/v1/credit-improvement/available-options"},
		{"wallet", func() error { _, err := c.CreditRisk.ConnectWallet(ctx, map[string]any{}); return err }, "POST /api/v1/credit-improvement/connect-wallet"},
		{"boosts", func() error { _, err := c.CreditRisk.ApplyBoosts(ctx, map[string]any{}); return err }, "POST /api/v1/credit-improvement/apply-boosts"},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			if err := tc.call(); err != nil {
				t.Fatalf("call failed: %v", err)
			}
			if seen != tc.want {
				t.Errorf("got %q, want %q", seen, tc.want)
			}
		})
	}
}

func TestCorePaths(t *testing.T) {
	var seen string
	srv := testServer(t, &seen)
	defer srv.Close()
	c := testClient(srv)
	withToken(c)
	ctx := context.Background()

	if _, err := c.Orders.List(ctx, 1, 20, ""); err != nil {
		t.Fatal(err)
	}
	if seen != "GET /api/v1/orders" {
		t.Errorf("got %q", seen)
	}
	if _, err := c.Storefront.Search(ctx, "gpu", 10, true); err != nil {
		t.Fatal(err)
	}
	if !strings.HasPrefix(seen, "GET /api/v1/storefront/search") {
		t.Errorf("got %q", seen)
	}
	if _, err := c.PriceDrops.List(ctx, 10, 5, 7); err != nil {
		t.Fatal(err)
	}
	if seen != "GET /api/v1/price-drops" {
		t.Errorf("got %q", seen)
	}
}
