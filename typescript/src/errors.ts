/** SDK error classes. */

export class HuntrechtError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
    public readonly response?: unknown,
  ) {
    super(message);
    this.name = 'HuntrechtError';
  }
}

export class AuthenticationError extends HuntrechtError {
  constructor(message: string, status?: number, response?: unknown) {
    super(message, status, response);
    this.name = 'AuthenticationError';
  }
}

export class RateLimitError extends HuntrechtError {
  constructor(
    message: string,
    public readonly retryAfter: number = 60,
    status?: number,
    response?: unknown,
  ) {
    super(message, status, response);
    this.name = 'RateLimitError';
  }
}

export class NotFoundError extends HuntrechtError {
  constructor(message: string, status?: number, response?: unknown) {
    super(message, status, response);
    this.name = 'NotFoundError';
  }
}

export class ValidationError extends HuntrechtError {
  constructor(message: string, status?: number, response?: unknown) {
    super(message, status, response);
    this.name = 'ValidationError';
  }
}

export class PermissionError extends HuntrechtError {
  constructor(message: string, status?: number, response?: unknown) {
    super(message, status, response);
    this.name = 'PermissionError';
  }
}
