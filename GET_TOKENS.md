# Getting API Tokens

## Plex Token (Official Plex Method)

Follow the official Plex documentation: https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/

### Quick Summary:

**Option 1: Plex Web Settings (Easiest)**
1. Open Plex Web: `http://YOUR-PLEX-IP:32400/web`
2. Click your profile icon (top right)
3. Click "Settings"
4. Click "Account" in left menu
5. Scroll to "Authorized Devices"
6. Click the "Show Token" button
7. Copy your token

**Option 2: Browser Inspector (If Option 1 doesn't work)**
1. Open Plex Web: `http://YOUR-PLEX-IP:32400/web`
2. Press F12 to open Developer Tools
3. Go to "Storage" or "Application" tab
4. Click "Cookies"
5. Look for `auth-token` or `myPlexAccessToken`
6. Copy the value

**Option 3: Access Library XML (Alternative)**
Visit this URL in your browser:
```
http://YOUR-PLEX-IP:32400/library/sections
```

If the page loads, you have API access. You can also:
1. Right-click → "Save Page As"
2. Save as `plex.xml`
3. Open in text editor
4. Look for token references

**Option 4: Check Plex Config Files**

On your Plex server machine:

**Linux:**
```bash
grep PlexOnlineToken ~/.plex/Plex\ Media\ Server/Preferences.xml
```

**Windows:**
```
C:\Users\[YourUsername]\AppData\Local\Plex Media Server\Preferences.xml
```

Search for `PlexOnlineToken` attribute

**macOS:**
```bash
grep PlexOnlineToken ~/Library/Application\ Support/Plex\ Media\ Server/Preferences.xml
```

**Docker:**
```bash
docker exec plex grep PlexOnlineToken /config/Library/Application\ Support/Plex\ Media\ Server/Preferences.xml
```

### Step 5: Use It

Paste the token into the Plex API Token field in the setup.

---

## If the XML Method Doesn't Work

### Method 2: Check Plex Web (Sometimes Works)

1. Open Plex Web (your Plex server interface)
2. Sign in
3. Look in Settings > Remote Access
4. The token might be shown there (usually not, but worth checking)

### Method 3: Use Browser Tools

1. Open Plex Web
2. Right-click → Inspect (F12)
3. Go to Network tab
4. Reload page
5. Look for requests - the token might be in headers

### Method 4: Check Server Logs

Plex logs sometimes contain the token. Location varies by OS:
- **Linux:** `/var/lib/plexmediaserver/Library/Logs/`
- **Docker:** Check docker logs
- **Synology:** `/var/packages/PlexMediaServer/target/Library/Logs/`

---

## Overseerr Token (This One is Easy)

### Step 1: Open Overseerr

Go to your Overseerr instance (e.g., `http://192.168.1.100:5055`)

### Step 2: Go to Settings

Click Settings in the bottom left

### Step 3: API Keys

Click "API Keys" (usually in the left menu)

### Step 4: Create Key

Click "Create API Key" button

### Step 5: Copy Token

Copy the generated key and use it

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

## Common Issues

### "Can't access http://YOUR-PLEX-IP:32400/identity"

**Solutions:**
- Make sure Plex is running
- Check the IP address is correct
- Try `localhost:32400` if on same machine
- Try `plex.local:32400` if on local network
- Check firewall isn't blocking port 32400

### "I don't see a token in the XML"

**Solutions:**
- Make sure you're authenticated in Plex
- Try logging out of Plex and back in
- Try a different browser
- The token should be in the first XML response

### "Token doesn't work in the tool"

**Solutions:**
- Copy the token again carefully (no extra spaces)
- Make sure you're using the right token (Plex vs Overseerr)
- Check the IP addresses are correct
- Click "Test Connection" to see the exact error
- Make sure Plex/Overseerr are running

### "Test Connection fails but token looks right"

**Solutions:**
- Check Plex/Overseerr URLs are correct
- Make sure ports are right (32400 for Plex, 5055 for Overseerr)
- Check firewall allows the connections
- Try from the machine running the tool
- Look at the error message carefully

---

## URLs Needed

You'll also need these URLs configured:

**Plex:**
- `http://192.168.1.100:32400` (or your IP)
- `http://plex.local:32400` (if using local hostname)
- `http://localhost:32400` (if tool is on same machine)

**Overseerr:**
- `http://192.168.1.100:5055` (or your IP)
- `http://overseerr.local:5055` (if using local hostname)
- `http://localhost:5055` (if tool is on same machine)

Include `http://` or `https://` at the start!

---

## Summary

1. **Plex Token:** Visit `http://YOUR-PLEX-IP:32400/identity` → Find `token="..."` in XML
2. **Overseerr Token:** Settings → API Keys → Create API Key
3. **Test:** Click "Test Connection" in the tool
4. **Go:** Start using the tool!

That's it! 🚀
