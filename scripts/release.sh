#!/bin/bash
# Release SDK - tag, push, and trigger CI/CD publish workflows
#
# Usage:
#   ./scripts/release.sh python 0.1.1
#   ./scripts/release.sh typescript 0.2.0
#   ./scripts/release.sh go 0.1.0
#   ./scripts/release.sh ruby 0.1.0
#   ./scripts/release.sh rust 0.1.0
#
# This script:
#   1. Validates the SDK directory exists
#   2. Updates version in the SDK's package file
#   3. Creates a git tag (e.g., python/v0.1.1)
#   4. Pushes the tag to trigger the publish workflow

set -euo pipefail

SDK="${1:-}"
VERSION="${2:-}"

if [[ -z "$SDK" || -z "$VERSION" ]]; then
  echo "Usage: $0 <sdk> <version>"
  echo ""
  echo "SDKs: python, typescript, go, ruby, rust"
  echo "Version: semantic version (e.g., 0.1.0)"
  echo ""
  echo "Examples:"
  echo "  $0 python 0.1.1"
  echo "  $0 typescript 0.2.0"
  exit 1
fi

# Validate SDK
case "$SDK" in
  python|typescript|go|ruby|rust) ;;
  *)
    echo "Error: Unknown SDK '$SDK'. Must be: python, typescript, go, ruby, rust"
    exit 1
    ;;
esac

# Validate version format
if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$ ]]; then
  echo "Error: Invalid version '$VERSION'. Must be semantic version (e.g., 0.1.0)"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SDK_DIR="$(dirname "$SCRIPT_DIR")"
TAG="${SDK}/v${VERSION}"

# Check SDK directory exists
if [[ ! -d "$SDK_DIR/$SDK" ]]; then
  echo "Error: SDK directory '$SDK_DIR/$SDK' not found"
  exit 1
fi

# Update version in package file
echo "→ Updating version to $VERSION in sdk/$SDK..."
case "$SDK" in
  python)
    if command -v sed &>/dev/null; then
      sed -i "s/^version = \".*\"/version = \"$VERSION\"/" "$SDK_DIR/$SDK/pyproject.toml"
    fi
    ;;
  typescript)
    if command -v sed &>/dev/null; then
      sed -i "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" "$SDK_DIR/$SDK/package.json"
    fi
    ;;
  go)
    echo "  (Go uses git tags for versioning — no file update needed)"
    ;;
  ruby)
    if [[ -f "$SDK_DIR/$SDK/lib/huntrecht/version.rb" ]]; then
      sed -i "s/VERSION = \".*\"/VERSION = \"$VERSION\"/" "$SDK_DIR/$SDK/lib/huntrecht/version.rb"
    fi
    ;;
  rust)
    if command -v sed &>/dev/null; then
      sed -i "s/^version = \".*\"/version = \"$VERSION\"/" "$SDK_DIR/$SDK/Cargo.toml"
    fi
    ;;
esac

# Check if tag already exists
if git rev-parse "$TAG" &>/dev/null; then
  echo "Error: Tag '$TAG' already exists. Bump the version."
  exit 1
fi

# Commit version bump
echo "→ Committing version bump..."
git add "$SDK_DIR/$SDK/"
git commit -m "chore(sdk/$SDK): bump version to $VERSION" || true

# Create and push tag
echo "→ Creating tag $TAG..."
git tag -a "$TAG" -m "Release $SDK SDK v$VERSION"

echo "→ Pushing tag to trigger publish workflow..."
echo ""
echo "  git push origin $TAG"
echo ""
echo "This will trigger the GitHub Actions workflow:"
echo "  .github/workflows/publish-${SDK}.yml"
echo ""
echo "After the workflow completes, the SDK will be published to:"
case "$SDK" in
  python)     echo "  PyPI: https://pypi.org/project/huntrecht-sdk/$VERSION" ;;
  typescript) echo "  npm:  https://www.npmjs.com/package/@huntrecht/sdk/v/$VERSION" ;;
  go)         echo "  Go:   https://pkg.go.dev/github.com/huntrecht/sdk-go@v$VERSION" ;;
  ruby)       echo "  RubyGems: https://rubygems.org/gems/huntrecht-sdk/versions/$VERSION" ;;
  rust)       echo "  crates.io: https://crates.io/crates/huntrecht-sdk/$VERSION" ;;
esac
echo ""
echo "→ Done! Monitor the workflow at:"
echo "  https://github.com/huntrecht/sdks/actions"
