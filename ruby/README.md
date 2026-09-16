# frozen_string_literal: true

# Huntrecht SDK for Ruby

Official Ruby client for the Huntrecht Platform API v1.

## Installation

```bash
gem install huntrecht-sdk
```

Or in your Gemfile:

```ruby
gem "huntrecht-sdk"
```

## Usage

```ruby
require "huntrecht"

client = Huntrecht::Client.new(
  client_id: "hnt_your_client_id",
  client_secret: "your_secret"
)

orders = client.orders.list(status: "pending")
```

See the [Ruby SDK docs](https://huntrecht.com/docs/sdks/ruby) for the full reference.
