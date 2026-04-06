.PHONY: generate generate-python generate-typescript generate-go generate-ruby generate-rust clean install-python install-typescript

PROTO_DIR := proto
GENERATED_DIR := generated
PROTO_FILES := $(wildcard $(PROTO_DIR)/huntrecht/v1/*.proto)

# Protoc plugins for each language
PYTHON_OUT := $(GENERATED_DIR)/python
TYPESCRIPT_OUT := $(GENERATED_DIR)/typescript
GO_OUT := $(GENERATED_DIR)/go
RUBY_OUT := $(GENERATED_DIR)/ruby
RUST_OUT := $(GENERATED_DIR)/rust

all: generate

generate: generate-python generate-typescript generate-go generate-ruby generate-rust

generate-python: $(PROTO_FILES)
	@mkdir -p $(PYTHON_OUT)
	@python -m grpc_tools.protoc \
		-I$(PROTO_DIR) \
		--python_out=$(PYTHON_OUT) \
		--pyi_out=$(PYTHON_OUT) \
		$^
	@touch $(PYTHON_OUT)/__init__.py
	@echo "✓ Python types generated"

generate-typescript: $(PROTO_FILES)
	@mkdir -p $(TYPESCRIPT_OUT)
	@npx protoc-gen-ts_proto \
		--plugin=protoc-gen-ts_proto \
		--ts_proto_out=$(TYPESCRIPT_OUT) \
		--ts_proto_opt=outputServices=false,esModuleInterop=true \
		-I$(PROTO_DIR) \
		$^
	@echo "✓ TypeScript types generated"

generate-go: $(PROTO_FILES)
	@mkdir -p $(GO_OUT)
	@protoc \
		-I$(PROTO_DIR) \
		--go_out=$(GO_OUT) \
		--go_opt=paths=source_relative \
		$^
	@echo "✓ Go types generated"

generate-ruby: $(PROTO_FILES)
	@mkdir -p $(RUBY_OUT)
	@protoc \
		-I$(PROTO_DIR) \
		--ruby_out=$(RUBY_OUT) \
		$^
	@echo "✓ Ruby types generated"

generate-rust: $(PROTO_FILES)
	@mkdir -p $(RUST_OUT)
	@echo "✓ Rust types generated (via build.rs)"

clean:
	rm -rf $(GENERATED_DIR)
	@echo "✓ Cleaned generated files"

install-python:
	cd python && pip install -e ".[dev]"

install-typescript:
	cd typescript && npm install
