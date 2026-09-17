# frozen_string_literal: true

module Huntrecht
  module Resources
    # Base class for all API resources.
    class Base
      def initialize(client)
        @client = client
      end

      private

      def request(method, path, **kwargs)
        @client.request(method, path, **kwargs)
      end

      def page_params(page, per_page, status = nil)
        params = { page: page, per_page: per_page }
        params[:status] = status if status
        params
      end

      # Accept a body as positional hash, kwargs, or both (Ruby 3
      # separates the two at call sites, so support each style).
      def body_for(data = nil, **kwargs)
        body = {}
        body.merge!(data) if data
        kwargs.each { |k, v| body[k.to_s] = v }
        body
      end
    end

    # OAuth2 token lifecycle.
    class AuthAPI < Base
      def token(grant_type: "client_credentials", client_id: nil, client_secret: nil,
                refresh_token: nil, scope: nil)
        body = { "grant_type" => grant_type }
        if grant_type == "client_credentials"
          body["client_id"] = client_id || @client.client_id
          body["client_secret"] = client_secret || @client.client_secret
          body["scope"] = scope if scope
        elsif grant_type == "refresh_token"
          body["refresh_token"] = refresh_token || @client.refresh_token || ""
        end
        data = request("POST", "/auth/token", json: body, auth_required: false)
        @client.store_tokens(data)
        data
      end

      def revoke(token = nil)
        tok = token || @client.access_token || ""
        request("POST", "/auth/revoke", params: { token: tok }, auth_required: false)
      end
    end

    # OAuth2 API clients.
    class ClientsAPI < Base
      def list(user_id)
        request("GET", "/clients", params: { user_id: user_id })
      end

      def create(user_id, data = nil, **kwargs)
        request("POST", "/clients", params: { user_id: user_id },
                                    json: body_for(data, **kwargs))
      end

      def update(user_id, client_id, data = nil, **kwargs)
        request("PATCH", "/clients/#{client_id}", params: { user_id: user_id },
                                                   json: body_for(data, **kwargs))
      end

      def rotate_secret(user_id, client_id)
        request("POST", "/clients/#{client_id}/rotate", params: { user_id: user_id })
      end

      def delete(user_id, client_id)
        request("DELETE", "/clients/#{client_id}", params: { user_id: user_id })
      end
    end

    # B2B trade orders.
    class OrdersAPI < Base
      def list(page: 1, per_page: 20, status: nil)
        request("GET", "/orders", params: page_params(page, per_page, status))
      end

      def get(order_id)
        request("GET", "/orders/#{order_id}")
      end

      def create(commodity:, quantity:, delivery_terms: "FOB", destination: nil, currency: "USD")
        params = { commodity: commodity, quantity: quantity,
                   delivery_terms: delivery_terms, currency: currency }
        params[:destination] = destination if destination
        request("POST", "/orders", params: params)
      end
    end

    # Payments.
    class PaymentsAPI < Base
      def list(page: 1, per_page: 20, status: nil)
        request("GET", "/payments", params: page_params(page, per_page, status))
      end

      def get(payment_id)
        request("GET", "/payments/#{payment_id}")
      end

      def create(data = nil, **kwargs)
        request("POST", "/payments", json: body_for(data, **kwargs))
      end
    end

    # B2B subscriptions.
    class SubscriptionsAPI < Base
      def list(page: 1, per_page: 20, status: nil, include_payment_history: false)
        params = page_params(page, per_page, status)
        params[:include_payment_history] = include_payment_history
        request("GET", "/subscriptions", params: params)
      end

      def get(subscription_id)
        request("GET", "/subscriptions/#{subscription_id}")
      end
    end

    # Basic credit scoring.
    class CreditAPI < Base
      def assess(data = nil, **kwargs)
        request("POST", "/credit/assess", json: body_for(data, **kwargs))
      end

      def score(customer_email)
        request("GET", "/credit/score/#{customer_email}")
      end
    end

    # Risk scoring, company assessments, improvement, credit history.
    class CreditRiskAPI < Base
      def get_score(customer_id)
        request("GET", "/credit-risk/score", params: { customer_id: customer_id })
      end

      def assess(data = nil, **kwargs)
        request("POST", "/credit-risk/assess", json: body_for(data, **kwargs))
      end

      def get_history(customer_id, limit: 20)
        request("GET", "/data-connect/credit-history",
                params: { customer_id: customer_id, limit: limit })
      end

      def get_assessment(user_id)
        request("GET", "/company/credit-assessment", params: { user_id: user_id })
      end

      def request_assessment(data = nil, **kwargs)
        request("POST", "/company/credit-assessment/request", json: body_for(data, **kwargs))
      end

      def get_improvement_options
        request("GET", "/credit-improvement/available-options")
      end

      def connect_wallet(data = nil, **kwargs)
        request("POST", "/credit-improvement/connect-wallet", json: body_for(data, **kwargs))
      end

      def apply_boosts(data = nil, **kwargs)
        request("POST", "/credit-improvement/apply-boosts", json: body_for(data, **kwargs))
      end
    end

    # KYC submissions.
    class KycAPI < Base
      def list(page: 1, per_page: 20, status: nil)
        request("GET", "/kyc", params: page_params(page, per_page, status))
      end

      def get(submission_id)
        request("GET", "/kyc/#{submission_id}")
      end

      def submit(data = nil, **kwargs)
        request("POST", "/kyc", json: body_for(data, **kwargs))
      end
    end

    # Commodity quotes.
    class QuotesAPI < Base
      def list(page: 1, per_page: 20)
        request("GET", "/quotes", params: { page: page, per_page: per_page })
      end

      def get(quote_id)
        request("GET", "/quotes/#{quote_id}")
      end

      def create(data = nil, **kwargs)
        request("POST", "/quotes", json: body_for(data, **kwargs))
      end
    end

    # User profiles.
    class UsersAPI < Base
      def me
        request("GET", "/users/me")
      end

      def get(user_id)
        request("GET", "/users/#{user_id}")
      end
    end

    # Shopify-backed catalog.
    class StorefrontAPI < Base
      def collections(first: 20, include_products: false)
        first = 100 if first > 100
        request("GET", "/storefront/collections",
                params: { first: first, include_products: include_products })
      end

      def collection(handle, products_first: 20)
        products_first = 250 if products_first > 250
        request("GET", "/storefront/collections/#{handle}",
                params: { products_first: products_first })
      end

      def products(first: 20, after: nil, b2b_only: false)
        first = 100 if first > 100
        params = { first: first, b2b_only: b2b_only }
        params[:after] = after if after
        request("GET", "/storefront/products", params: params)
      end

      def product(handle)
        request("GET", "/storefront/products/#{handle}")
      end

      def search(query, first: 10, b2b_only: false)
        first = 50 if first > 50
        request("GET", "/storefront/search",
                params: { query: query, first: first, b2b_only: b2b_only })
      end
    end

    # Price-drop events (public).
    class PriceDropsAPI < Base
      def list(limit: 10, min_discount: 5.0, days: 7)
        limit = 50 if limit > 50
        request("GET", "/price-drops",
                params: { limit: limit, min_discount: min_discount, days: days },
                auth_required: false)
      end

      def featured(limit: 10)
        limit = 10 if limit > 10
        request("GET", "/price-drops/featured", params: { limit: limit },
                                                auth_required: false)
      end
    end

    # Theme-safe proxy endpoints (public).
    class AppProxyAPI < Base
      def collections(first: 20, signature: nil)
        first = 100 if first > 100
        params = { first: first }
        params[:signature] = signature if signature
        request("GET", "/app-proxy/collections", params: params, auth_required: false)
      end

      def collection(handle, first: 20, signature: nil)
        first = 250 if first > 250
        params = { first: first }
        params[:signature] = signature if signature
        request("GET", "/app-proxy/collections/#{handle}", params: params,
                                                             auth_required: false)
      end

      def price_drops(limit: 10, min_discount: 5.0)
        limit = 20 if limit > 20
        request("GET", "/app-proxy/price-drops",
                params: { limit: limit, min_discount: min_discount },
                auth_required: false)
      end

      def payment_methods(customer_id: nil, product_price: 0, b2b_exclusive: false,
                          signature: nil)
        params = { product_price: product_price, b2b_exclusive: b2b_exclusive }
        params[:customer_id] = customer_id if customer_id
        params[:signature] = signature if signature
        request("GET", "/app-proxy/payment-methods", params: params,
                                                      auth_required: false)
      end
    end

    # Linked wallets and bank accounts.
    class LinkedPaymentsAPI < Base
      def check_eligibility(customer_id, product_price: 0, b2b_exclusive: false)
        request("GET", "/linked-payments/check-eligibility",
                params: { customer_id: customer_id, product_price: product_price,
                          b2b_exclusive: b2b_exclusive },
                auth_required: false)
      end

      def link_wallet(customer_id, wallet_address: nil, wallet_provider: nil)
        body = { "customer_id" => customer_id }
        body["wallet_address"] = wallet_address if wallet_address
        body["wallet_provider"] = wallet_provider if wallet_provider
        request("POST", "/linked-payments/link-wallet", json: body)
      end

      def link_bank(customer_id, plaid_access_token: nil, account_id: nil)
        body = { "customer_id" => customer_id }
        body["plaid_access_token"] = plaid_access_token if plaid_access_token
        body["account_id"] = account_id if account_id
        request("POST", "/linked-payments/link-bank", json: body)
      end

      def linked_accounts(customer_id)
        request("GET", "/linked-payments/linked-accounts/#{customer_id}")
      end
    end
  end
end
