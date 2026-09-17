# frozen_string_literal: true

module Huntrecht
  # Base error for all Huntrecht API failures.
  class APIError < StandardError
    attr_reader :status_code, :response

    def initialize(message = nil, status_code: nil, response: nil)
      super(message)
      @status_code = status_code
      @response = response
    end
  end

  # 401 — missing, expired, or invalid credentials.
  class AuthenticationError < APIError; end

  # 403 — authenticated but not permitted.
  class PermissionError < APIError; end

  # 404 — resource not found.
  class NotFoundError < APIError; end

  # 422 — request validation failed.
  class ValidationError < APIError; end

  # 429 — rate limited. Carries the Retry-After seconds.
  class RateLimitError < APIError
    attr_reader :retry_after

    def initialize(message = nil, status_code: 429, retry_after: 60, response: nil)
      super(message, status_code: status_code, response: response)
      @retry_after = retry_after
    end
  end
end
