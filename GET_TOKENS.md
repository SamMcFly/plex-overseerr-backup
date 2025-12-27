# Getting API Tokens

## Plex Token (XML Method - Most Reliable)

### Step 1: Access Plex Identity XML

Visit this URL in your browser (replace YOUR-PLEX-IP with your Plex server IP):

```
http://YOUR-PLEX-IP:32400/identity
```

**Examples:**
- `http://192.168.1.100:32400/identity`
- `http://plex.local:32400/identity`
- `http://localhost:32400/identity`

### Step 2: Find the Token

You'll see XML that looks like:

```xml
<MediaContainer friendlyName="My Plex Server" 
                 machineIdentifier="abc123def456ghi" 
                 version="1.24.5.5173">
  <Device name="Plex Web" 
           publicAddress="1.2.3.4" 
           token="YOUR_TOKEN_HERE_LONG_STRING" 
           protocolVersion="1" 
           protocolCapabilities="timeline,playback,navigation,playqueues"/>
</MediaContainer>
```

### Step 3: Copy Your Token

Find the `token="` part and copy the value after it.

**Example:**
```
token="xF2kP9nQ8mL7rJ4sT3vW"
```

The token is that long string of random characters.

### Step 4: Use It

Paste this token into the Plex API Token field in the tool.

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
