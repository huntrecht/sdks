# frozen_string_literal: true

require_relative "spec_helper"

# Captures requests instead of performing network I/O.
class CaptureClient < Huntrecht::Client
  attr_reader :calls

  def initialize(**kwargs)
    super
    @calls = []
  end

  def request(method, path, params: nil, json: nil, headers: nil, auth_required: true)
    if auth_required && @access_token.nil? && client_id.empty?
      raise Huntrecht::AuthenticationError,
            "No access token and no client credentials."
    end
    @calls << { method: method, path: path, params: params, json: json,
                auth_required: auth_required }
    {}
  end

  def last_call
    @calls.last
  end
end

FakeResp = Struct.new(:code, :body, :headers) do
  def [](key)
    headers[key]
  end
end

describe "Huntrecht Ruby SDK" do
  before do
    @client = CaptureClient.new(client_id: "id", client_secret: "secret")
  end

  it "exposes the version" do
    assert_match(/\A\d+\.\d+\.\d+/, Huntrecht::VERSION)
  end

  it "builds versioned URIs with query params" do
    uri = @client.build_uri("/orders", { page: 1, per_page: 20 })
    assert_equal "https://api.huntrecht.com/api/v1/orders?page=1&per_page=20", uri.to_s
  end

  it "trims trailing slashes from base_url" do
    c = CaptureClient.new(base_url: "https://example.com///")
    assert_equal "https://example.com", c.base_url
  end

  it "covers auth (2 ops)" do
    @client.auth.token
    assert_equal({ method: "POST", path: "/auth/token", params: nil,
                   json: { "grant_type" => "client_credentials",
                           "client_id" => "id", "client_secret" => "secret" },
                   auth_required: false }, @client.last_call)
    @client.auth.revoke("tok")
    assert_equal "POST", @client.last_call[:method]
    assert_equal "/auth/revoke", @client.last_call[:path]
  end

  it "covers clients (4 ops)" do
    @client.clients.list(7)
    assert_equal({ method: "GET", path: "/clients", params: { user_id: 7 },
                   json: nil, auth_required: true }, @client.last_call)
    @client.clients.create(7, { "name" => "x" })
    assert_equal "POST", @client.last_call[:method]
    @client.clients.rotate_secret(7, "c1")
    assert_equal "/clients/c1/rotate", @client.last_call[:path]
    @client.clients.delete(7, "c1")
    assert_equal "DELETE", @client.last_call[:method]
  end

  it "covers orders, payments, subscriptions" do
    @client.orders.list(status: "pending")
    assert_equal "/orders", @client.last_call[:path]
    @client.orders.get("o1")
    assert_equal "/orders/o1", @client.last_call[:path]
    @client.orders.create(commodity: "Gold", quantity: 100)
    assert_equal "POST", @client.last_call[:method]

    @client.payments.list
    assert_equal "/payments", @client.last_call[:path]
    @client.payments.get("p1")
    assert_equal "/payments/p1", @client.last_call[:path]
    @client.payments.create({ "amount" => 10 })
    assert_equal "POST", @client.last_call[:method]

    @client.subscriptions.list
    assert_equal "/subscriptions", @client.last_call[:path]
    @client.subscriptions.get("s1")
    assert_equal "/subscriptions/s1", @client.last_call[:path]
  end

  it "covers credit and credit risk (10 ops)" do
    @client.credit.assess({ "a" => 1 })
    assert_equal "/credit/assess", @client.last_call[:path]
    @client.credit.score("a@b.c")
    assert_equal "/credit/score/a@b.c", @client.last_call[:path]

    @client.credit_risk.get_score("c")
    assert_equal "/credit-risk/score", @client.last_call[:path]
    @client.credit_risk.assess({})
    assert_equal "/credit-risk/assess", @client.last_call[:path]
    @client.credit_risk.get_history("c")
    assert_equal "/data-connect/credit-history", @client.last_call[:path]
    @client.credit_risk.get_assessment("u")
    assert_equal "/company/credit-assessment", @client.last_call[:path]
    @client.credit_risk.request_assessment({})
    assert_equal "/company/credit-assessment/request", @client.last_call[:path]
    @client.credit_risk.get_improvement_options
    assert_equal "/credit-improvement/available-options", @client.last_call[:path]
    @client.credit_risk.connect_wallet({})
    assert_equal "/credit-improvement/connect-wallet", @client.last_call[:path]
    @client.credit_risk.apply_boosts({})
    assert_equal "/credit-improvement/apply-boosts", @client.last_call[:path]
  end

  it "covers kyc, quotes, users" do
    @client.kyc.list
    assert_equal "/kyc", @client.last_call[:path]
    @client.kyc.get("k1")
    assert_equal "/kyc/k1", @client.last_call[:path]
    @client.kyc.submit({})
    assert_equal "POST", @client.last_call[:method]

    @client.quotes.get("q1")
    assert_equal "/quotes/q1", @client.last_call[:path]
    @client.quotes.create({})
    assert_equal "/quotes", @client.last_call[:path]

    @client.users.me
    assert_equal "/users/me", @client.last_call[:path]
    @client.users.get("u1")
    assert_equal "/users/u1", @client.last_call[:path]
  end

  it "covers storefront (5 ops)" do
    @client.storefront.collections
    assert_equal "/storefront/collections", @client.last_call[:path]
    @client.storefront.collection("h")
    assert_equal "/storefront/collections/h", @client.last_call[:path]
    @client.storefront.products
    assert_equal "/storefront/products", @client.last_call[:path]
    @client.storefront.product("h")
    assert_equal "/storefront/products/h", @client.last_call[:path]
    @client.storefront.search("copper")
    assert_equal "/storefront/search", @client.last_call[:path]
  end

  it "covers price drops and app proxy (6 ops, public)" do
    @client.price_drops.list
    assert_equal false, @client.last_call[:auth_required]
    assert_equal "/price-drops", @client.last_call[:path]
    @client.price_drops.featured
    assert_equal "/price-drops/featured", @client.last_call[:path]

    @client.app_proxy.collections
    assert_equal "/app-proxy/collections", @client.last_call[:path]
    @client.app_proxy.collection("h")
    assert_equal "/app-proxy/collections/h", @client.last_call[:path]
    @client.app_proxy.price_drops
    assert_equal "/app-proxy/price-drops", @client.last_call[:path]
    @client.app_proxy.payment_methods
    assert_equal "/app-proxy/payment-methods", @client.last_call[:path]
  end

  it "covers linked payments (4 ops)" do
    @client.linked_payments.check_eligibility("c1")
    assert_equal "/linked-payments/check-eligibility", @client.last_call[:path]
    assert_equal false, @client.last_call[:auth_required]
    @client.linked_payments.link_wallet("c1", wallet_address: "0x0")
    assert_equal "/linked-payments/link-wallet", @client.last_call[:path]
    @client.linked_payments.link_bank("c1")
    assert_equal "/linked-payments/link-bank", @client.last_call[:path]
    @client.linked_payments.linked_accounts("c1")
    assert_equal "/linked-payments/linked-accounts/c1", @client.last_call[:path]
  end

  it "accepts kwargs bodies as documented" do
    @client.payments.create(subscription_id: 123, amount: 2500.00, currency: "USD")
    assert_equal({ "subscription_id" => 123, "amount" => 2500.00,
                   "currency" => "USD" }, @client.last_call[:json])

    @client.credit.assess(customer_email: "a@b.c", include_recommendations: true)
    assert_equal "/credit/assess", @client.last_call[:path]

    @client.kyc.submit(company_name: "Acme Corp", company_type: "LLC")
    assert_equal "POST", @client.last_call[:method]

    @client.quotes.create(commodity: "Copper", quantity: 500, unit: "kg")
    assert_equal "/quotes", @client.last_call[:path]

    @client.orders.create(commodity: "Gold", quantity: 100, destination: "New York")
    assert_equal "New York", @client.last_call[:params][:destination]
  end

  it "maps HTTP errors to typed exceptions" do
    err = assert_raises(Huntrecht::AuthenticationError) do
      @client.send(:handle_response, FakeResp.new("401", '{"error_description":"bad"}', {}))
    end
    assert_equal 401, err.status_code

    assert_raises(Huntrecht::NotFoundError) do
      @client.send(:handle_response, FakeResp.new("404", "{}", {}))
    end
    rl = assert_raises(Huntrecht::RateLimitError) do
      @client.send(:handle_response, FakeResp.new("429", "{}", { "Retry-After" => "5" }))
    end
    assert_equal 5, rl.retry_after
  end

  it "raises without credentials" do
    assert_raises(Huntrecht::AuthenticationError) do
      CaptureClient.new.request("GET", "/orders")
    end
  end
end
