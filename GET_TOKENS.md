# Getting API Tokens

## Plex Token (Official Plex Method)

Follow the official Plex documentation to obtain your authentication token:

**Official Plex Documentation:** https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/

Once you have obtained your token from the official Plex documentation, paste it into the Plex API Token field in the setup.

---

## Overseerr Token

### Step 1: Open Overseerr

Go to your Overseerr instance (e.g., `http://192.168.1.100:5055`)

### Step 2: Go to Settings

Click Settings in the bottom left

### Step 3: API Keys

Click "API Keys" (usually in the left menu)

### Step 4: Create Key

Click "Create API Key" button

### Step 5: Copy Token

Copy the generated key and use it in the setup

---

## Testing Your Tokens

### In the Tool

Click "Test Connection" in the Setup tab - it will verify both tokens work.

### Manual Testing (Command Line)

**Plex:**
```bash
curl -H "X-Plex-Token: YOUR_PLEX_TOKEN" \
  http://YOUR-PLEX-IP:32400/library/sections
```

If it works, you'll see XML output. If token is wrong, you'll get an error.

**Overseerr:**
```bash
curl -H "X-Api-Key: YOUR_OVERSEERR_TOKEN" \
  http://YOUR-OVERSEERR-IP:5055/api/v1/user
```

If it works, you'll see JSON output with user info.

---

## Troubleshooting

### Token doesn't work in the tool

**Solutions:**
- Copy the token again carefully (no extra spaces)
- Make sure you're using the correct token
- Check the Plex and Overseerr URLs are correct
- Click "Test Connection" to see the exact error message
- Verify Plex and Overseerr are running and accessible

### Can't reach Plex/Overseerr

**Check:**
- Plex is running on port 32400
- Overseerr is running on port 5055
- Firewall allows connections
- IP addresses are correct
- URLs include `http://` or `https://`

---

## URLs Format

**Plex:**
- `http://192.168.1.100:32400` (IP address)
- `http://plex.local:32400` (local hostname)
- `http://localhost:32400` (same machine)
- `https://plex.yourdomain.com` (with SSL)

**Overseerr:**
- `http://192.168.1.100:5055` (IP address)
- `http://overseerr.local:5055` (local hostname)
- `http://localhost:5055` (same machine)
- `https://overseerr.yourdomain.com` (with SSL)

Include `http://` or `https://` at the start!

---

## Summary

1. **Plex Token:** Get from official Plex documentation
2. **Overseerr Token:** Settings → API Keys → Create API Key
3. **Test:** Click "Test Connection" in the tool
4. **Go:** Start using the tool!

That's it! 🚀
