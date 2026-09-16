# frozen_string_literal: true

require_relative "lib/huntrecht/version"

Gem::Specification.new do |spec|
  spec.name = "huntrecht-sdk"
  spec.version = Huntrecht::VERSION
  spec.authors = ["Huntrecht"]
  spec.email = ["dev@huntrecht.com"]

  spec.summary = "Official Ruby SDK for the Huntrecht Platform API v1"
  spec.description = "B2B commerce, credit risk, KYC, quotes, storefront, and payments for the Huntrecht Platform API v1."
  spec.homepage = "https://github.com/huntrecht/sdks"
  spec.license = "MIT"

  spec.required_ruby_version = ">= 3.0"

  spec.files = Dir["lib/**/*.rb", "README.md", "LICENSE*"]
  spec.require_paths = ["lib"]

  spec.metadata["homepage_uri"] = spec.homepage
  spec.metadata["source_code_uri"] = spec.homepage
end
