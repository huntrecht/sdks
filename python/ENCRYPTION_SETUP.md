# Credit History Encryption Setup

## Overview

The GraphQL Data Connect SDK encrypts sensitive financial PII (emails, account numbers) using **Fernet symmetric encryption** before storing in PostgreSQL.

## ⚠️ CRITICAL REQUIREMENT

**The same encryption key MUST be used across ALL server restarts.**

If you lose the encryption key or use a different one after restart, all previously encrypted data becomes **permanently unreadable**.

## Setup Instructions

### 1. Generate an Encryption Key

Run this command to generate a secure Fernet key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

This will output a 44-character string like:
```
pXzK9vQ7jR3mN6wE5tY8uI1oP4aS2dF7gH0jK9lM3nB=
```

### 2. Set as Environment Variable

**For Development (Replit):**
1. Go to your Replit project
2. Click "Secrets" (lock icon in left sidebar)
3. Add a new secret:
   - **Key**: `CREDIT_HISTORY_ENCRYPTION_KEY`
   - **Value**: `<your-generated-key-from-step-1>`

**For Production:**
```bash
export CREDIT_HISTORY_ENCRYPTION_KEY="pXzK9vQ7jR3mN6wE5tY8uI1oP4aS2dF7gH0jK9lM3nB="
```

### 3. Secure Storage

🔐 **STORE THIS KEY SECURELY!**

- Add to password manager
- Store in secure secrets management system (AWS Secrets Manager, HashiCorp Vault, etc.)
- **NEVER** commit to git or share publicly
- Treat it like a database password

## Verification

After setting the key, restart your server. You should see:
```
✅ Credit history encryption initialized successfully
```

If you see an error:
```
❌ CREDIT_HISTORY_ENCRYPTION_KEY environment variable is required!
```

Then the key is not set correctly.

## Key Rotation (Advanced)

If you need to rotate the encryption key:

1. **Generate new key**:
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

2. **Re-encrypt all existing data**:
   ```sql
   -- This requires a custom migration script
   -- Contact your DBA or run the provided rotation script
   ```

3. **Update environment variable** with the new key

4. **Restart all servers**

## Troubleshooting

### Error: "Decryption failed (key mismatch or corrupt data)"

**Cause**: You're using a different encryption key than the one used to encrypt the data.

**Solution**: 
1. Find the original key used during initial setup
2. Set `CREDIT_HISTORY_ENCRYPTION_KEY` to that value
3. Restart the server

### Error: "Invalid CREDIT_HISTORY_ENCRYPTION_KEY length"

**Cause**: The key is not 44 characters (invalid Fernet key format).

**Solution**: Generate a new key using the command in Step 1 above.

## Security Best Practices

✅ **DO:**
- Generate a strong random key
- Store key in secure secrets manager
- Use the same key across all environments (dev, staging, prod should have different keys)
- Back up the key securely

❌ **DON'T:**
- Use weak or predictable keys
- Share keys in chat/email
- Commit keys to version control
- Reuse keys across different projects

## Data Encryption Scope

The following fields are encrypted at rest:

| Field | Encryption | Display |
|-------|-----------|---------|
| `email` | ✅ Encrypted | Masked: `****@example.com` |
| `account_number` | ✅ Encrypted | Masked: `****1234` |
| RAG documents | ❌ PII removed completely | No PII in vector store |

## Production Deployment Checklist

- [ ] Generate encryption key
- [ ] Set `CREDIT_HISTORY_ENCRYPTION_KEY` in production secrets
- [ ] Verify server starts successfully
- [ ] Test ingestion of sample credit history
- [ ] Restart server and verify data is still decryptable
- [ ] Set up key backup procedure
- [ ] Document key recovery process

---

**Questions?** Check the main [README.md](README.md) or consult your security team.
