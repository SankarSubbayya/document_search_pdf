# 🔧 Troubleshooting Connection Issues

## Your Current Status ✅
- **Streamlit App**: Running on port 8512 (PID: 98686)
- **Qdrant**: Running on port 6333
- **Server Response**: HTTP 200 OK

The services are running correctly! The issue is likely browser or network-related.

## 🚀 Quick Fix Solutions

### 1. Try Different URLs (in order)
```bash
# Option 1: Localhost (most common)
http://localhost:8512

# Option 2: 127.0.0.1
http://127.0.0.1:8512

# Option 3: 0.0.0.0
http://0.0.0.0:8512

# Option 4: Your local IP (shown in terminal)
http://10.42.70.95:8512
```

### 2. Clear Browser Cache
- **Chrome/Edge**: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
- **Safari**: Cmd+Option+E then Cmd+R
- **Firefox**: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)

### 3. Try Different Browser
Sometimes browsers cache redirect errors. Try:
- Chrome
- Safari
- Firefox
- Edge

### 4. Check for Port Conflicts
```bash
# Kill existing process and restart
kill 98686

# Restart with explicit settings
uv run streamlit run apps/pdf_manager_app.py --server.port 8512 --server.address localhost
```

### 5. Use a Different Port
```bash
# Try port 8513 instead
uv run streamlit run apps/pdf_manager_app.py --server.port 8513

# Then access:
http://localhost:8513
```

## 🔍 Diagnostic Commands

### Check App Status
```bash
# Verify app is responding
curl http://localhost:8512

# Check what's listening on the port
lsof -i :8512

# Check process status
ps aux | grep 98686
```

### Test Connection
```bash
# Test if localhost resolves correctly
ping localhost

# Check network interface
ifconfig | grep inet

# Test with curl
curl -v http://localhost:8512 2>&1 | head -20
```

## 🔄 Full Restart Procedure

If above doesn't work, do a complete restart:

```bash
# 1. Kill all Streamlit processes
pkill -f streamlit

# 2. Clear any port blocks
lsof -ti:8512 | xargs kill -9 2>/dev/null

# 3. Restart Qdrant (if needed)
docker restart qdrant 2>/dev/null || docker start qdrant

# 4. Start fresh with explicit settings
uv run streamlit run apps/pdf_manager_app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true

# 5. Access at:
http://localhost:8501
```

## 🌐 Network Issues

### Firewall/Security Software
Check if firewall is blocking:
```bash
# macOS
sudo pfctl -s info

# Check system preferences > Security & Privacy > Firewall
```

### VPN Interference
If using VPN:
1. Try disconnecting VPN
2. Access the app
3. Or configure VPN to allow local connections

### Proxy Settings
Check browser proxy:
1. Chrome: Settings → Advanced → System → Proxy settings
2. Ensure "localhost" and "127.0.0.1" are in bypass list

## 🎯 Alternative Access Methods

### 1. Network URL
The app provides multiple URLs:
```
Local URL: http://localhost:8512          # Use this first
Network URL: http://10.42.70.95:8512      # Try if localhost fails
External URL: http://136.152.214.107:8512 # For external access
```

### 2. SSH Tunnel (if remote)
```bash
# If running on remote server
ssh -L 8512:localhost:8512 your-server
# Then access locally at http://localhost:8512
```

## ✅ Verification Steps

1. **Check Terminal Output**
   Look for:
   ```
   You can now view your Streamlit app in your browser.
   Local URL: http://localhost:8512
   ```

2. **No Error Messages**
   Ensure no Python errors in terminal

3. **Browser Console**
   - Open Developer Tools (F12)
   - Check Console tab for errors
   - Check Network tab for failed requests

## 🔴 Common Error Messages

### "This site can't be reached"
- Service is not running on expected port
- Try the URLs listed above

### "Connection refused"
- Port is blocked or app crashed
- Restart the application

### "ERR_CONNECTION_RESET"
- Firewall or security software issue
- Check security settings

## 💡 Quick Test

Run this simple test:
```bash
# Create test app
echo "import streamlit as st; st.write('Test')" > test_app.py

# Run it
uv run streamlit run test_app.py --server.port 8888

# Access at http://localhost:8888
```

If this works, the issue is with the specific app, not Streamlit.

## 🆘 Still Not Working?

1. **Restart your computer** (clears all port bindings)
2. **Check system logs**: `Console.app` on macOS
3. **Try without UV**: `streamlit run apps/pdf_manager_app.py`
4. **Check Python environment**: `which python3`

The app IS running (confirmed by diagnostics), so it's definitely accessible - we just need to find the right way to connect to it!