# frozen_string_literal: true

require "net/http"
require "uri"
require "json"

require_relative "errors"
require_relative "version"

module Huntrecht
  API_VERSION = "v1"
  DEFAULT_BASE_URL = "https://api.huntrecht.com"
  USER_AGENT = "huntrecht-sdk-ruby/#{VERSION}"

  # Client for the Huntrecht Platform API v1.
  #
  #   client = Huntrecht::Client.new(
  #     client_id: "hnt_abc123",
  #     client_secret: "secret"
  #   )
  #   client.auth.token # authenticate
  #   orders = client.orders.list
  class Client
    attr_reader :base_url, :client_id, :timeout, :max_retries, :retry_backoff
    attr_accessor :access_token

    def initialize(base_url: nil, client_id: nil, client_secret: nil,
                   access_token: nil, timeout: 30, max_retries: 3,
                   retry_backoff: 1.0)
      @base_url = (base_url || ENV["HUNTRECHT_BASE_URL"] || DEFAULT_BASE_URL).sub(%r{/+\z}, "")
      @client_id = client_id || ENV["HUNTRECHT_CLIENT_ID"] || ""
      @client_secret = client_secret || ENV["HUNTRECHT_CLIENT_SECRET"] || ""
      @access_token = access_token
      @refresh_token = nil
      @token_expires_at = Time.at(0)
      @timeout = timeout
      @max_retries = max_retries
      @retry_backoff = retry_backoff

      require_relative "resources"
      @auth = Resources::AuthAPI.new(self)
      @clients = Resources::ClientsAPI.new(self)
      @orders = Resources::OrdersAPI.new(self)
      @payments = Resources::PaymentsAPI.new(self)
      @subscriptions = Resources::SubscriptionsAPI.new(self)
      @credit = Resources::CreditAPI.new(self)
      @credit_risk = Resources::CreditRiskAPI.new(self)
      @kyc = Resources::KycAPI.new(self)
      @quotes = Resources::QuotesAPI.new(self)
      @users = Resources::UsersAPI.new(self)
      @storefront = Resources::StorefrontAPI.new(self)
      @price_drops = Resources::PriceDropsAPI.new(self)
      @app_proxy = Resources::AppProxyAPI.new(self)
      @linked_payments = Resources::LinkedPaymentsAPI.new(self)
    end

    attr_reader :auth, :clients, :orders, :payments, :subscriptions,
                :credit, :credit_risk, :kyc, :quotes, :users, :storefront,
                :price_drops, :app_proxy, :linked_payments

    def client_secret
      @client_secret
    end

    def refresh_token
      @refresh_token
    end

    def store_tokens(data)
      @access_token = data["access_token"]
      @refresh_token = data["refresh_token"]
      @token_expires_at = Time.now + (data["expires_in"] || 1800).to_i - 60
    end

    # Make an API request with automatic auth, retry, and rate-limit handling.
    def request(method, path, params: nil, json: nil, headers: nil, auth_required: true)
      ensure_token if auth_required

      last_error = nil
      (0..@max_retries).each do |attempt|
        begin
          return perform(method, path, params: params, json: json,
                         headers: headers, auth_required: auth_required)
        rescue RateLimitError => e
          last_error = e
          raise if attempt >= @max_retries

          wait = e.retry_after.positive? ? e.retry_after : @retry_backoff * (2**attempt)
          sleep(wait)
        rescue APIError
          raise
        rescue StandardError => e
          last_error = APIError.new("HTTP error: #{e.message}")
          raise last_error if attempt >= @max_retries

          sleep(@retry_backoff * (2**attempt))
        end
      end
      raise(last_error || APIError.new("Request failed"))
    end

    # Build the full URI for a path + query params (no network).
    def build_uri(path, params = nil)
      uri = URI("#{@base_url}/api/#{API_VERSION}#{path}")
      clean = (params || {}).reject { |_k, v| v.nil? }
      unless clean.empty?
        uri.query = URI.encode_www_form(clean.map { |k, v| [k.to_s, v.to_s] })
      end
      uri
    end

    private

    def ensure_token
      return if @access_token && Time.now < @token_expires_at

      if !@client_id.empty? && !@client_secret.empty?
        data = @auth.token
        store_tokens(data)
      else
        raise AuthenticationError, "No access token and no client credentials. " \
                                   "Set HUNTRECHT_CLIENT_ID and HUNTRECHT_CLIENT_SECRET, " \
                                   "or pass them to Huntrecht::Client.new."
      end
    end

    def perform(method, path, params:, json:, headers:, auth_required:)
      uri = build_uri(path, params)
      http = Net::HTTP.new(uri.host, uri.port)
      http.use_ssl = uri.scheme == "https"
      http.open_timeout = @timeout
      http.read_timeout = @timeout

      req_class = {
        "GET" => Net::HTTP::Get, "POST" => Net::HTTP::Post,
        "PUT" => Net::HTTP::Put, "PATCH" => Net::HTTP::Patch,
        "DELETE" => Net::HTTP::Delete
      }.fetch(method.upcase) { raise APIError, "Unsupported method #{method}" }

      req = req_class.new(uri.request_uri)
      req["Accept"] = "application/json"
      req["User-Agent"] = USER_AGENT
      req["Authorization"] = "Bearer #{@access_token}" if auth_required && @access_token
      (headers || {}).each { |k, v| req[k] = v }
      if json
        req["Content-Type"] = "application/json"
        req.body = JSON.generate(json)
      end

      handle_response(http.request(req))
    end

    def handle_response(resp)
      return {} if resp.code == "204"

      data = begin
        JSON.parse(resp.body || "")
      rescue JSON::ParserError
        { "raw" => resp.body.to_s }
      end

      case resp.code.to_i
      when 200..299
        data
      when 401
        @access_token = nil
        raise AuthenticationError.new(data["error_description"] || "Authentication failed",
                                      status_code: 401, response: data)
      when 403
        raise PermissionError.new(data["error_description"] || "Insufficient permissions",
                                  status_code: 403, response: data)
      when 404
        raise NotFoundError.new(data["error_description"] || "Resource not found",
                                status_code: 404, response: data)
      when 422
        raise ValidationError.new(data["error_description"] || "Validation failed",
                                  status_code: 422, response: data)
      when 429
        retry_after = resp["Retry-After"].to_i
        retry_after = 60 if retry_after <= 0
        raise RateLimitError.new(data["error_description"] || "Rate limit exceeded",
                                 status_code: 429, retry_after: retry_after, response: data)
      else
        raise APIError.new(data["error_description"] || "HTTP #{resp.code}",
                           status_code: resp.code.to_i, response: data)
      end
    end
  end
end
