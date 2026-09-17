# frozen_string_literal: true

# Huntrecht Platform SDK for Ruby.
#
# Official client for the Huntrecht Platform API v1.
#
#   require "huntrecht"
#
#   client = Huntrecht::Client.new(
#     client_id: "hnt_your_client_id",
#     client_secret: "your_secret"
#   )
#   orders = client.orders.list
require_relative "huntrecht/version"
require_relative "huntrecht/errors"
require_relative "huntrecht/client"
