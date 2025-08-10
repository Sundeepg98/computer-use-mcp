# Critical MCP stderr Issue & Fix

## 🚨 The Problem

**Claude treats ALL stderr output from MCP servers as real errors**, even INFO logs!

### What Happens:
```python
# Your MCP server logs:
logger.info("Starting MCP server...")  # Goes to stderr

# Claude sees:
"⚠️ ERROR from MCP server: Starting MCP server..."

# User thinks:
"Something is broken!"
```

## 🔴 Bad Practice (What We Had):
```python
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr  # ❌ Claude treats this as errors!
)
```

## ✅ The Fix (What We Changed):
```python
# Log to file for debugging
logging.basicConfig(
    level=logging.INFO,
    filename='/tmp/mcp_server.log',  # ✅ Logs go to file
    filemode='a'
)

# Only send CRITICAL errors to stderr
stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setLevel(logging.CRITICAL)  # ✅ Only real errors
logging.getLogger().addHandler(stderr_handler)
```

## 📊 Impact:

| Before | After |
|--------|-------|
| Every log → stderr → Claude error | INFO → file, CRITICAL → stderr |
| User sees false errors | User sees only real problems |
| Confusing experience | Clean experience |

## 🛠️ Implementation Options:

### Option 1: File Logging (Recommended)
```python
# All logs to file, only critical to stderr
log_file = os.environ.get('MCP_LOG_FILE', '/tmp/mcp.log')
logging.basicConfig(filename=log_file)
```

### Option 2: Suppress All stderr
```python
# Silence everything except JSON responses
sys.stderr = open(os.devnull, 'w')
```

### Option 3: Structured Logging
```python
# Use JSON for everything
def log_event(level, message):
    # Don't use stderr, use JSON response
    return {"log": {"level": level, "message": message}}
```

## 🎯 Best Practices for MCP Servers:

1. **NEVER log INFO/DEBUG to stderr**
2. **Use files or structured responses for logs**
3. **Reserve stderr for CRITICAL failures only**
4. **Test with Claude to verify clean output**
5. **Document this for other developers**

## 🤔 Why Sentry MCP Might Help:

- Centralizes error handling
- Separates logs from MCP protocol
- Provides structured error tracking
- BUT: Doesn't directly fix stderr issue

## 📝 Testing Your Fix:

```bash
# Before fix:
python3 src/mcp/mcp_server.py 2>&1 | grep -c "INFO"
# Result: Many INFO lines in stderr

# After fix:
python3 src/mcp/mcp_server.py 2>&1 | grep -c "INFO"
# Result: 0 (INFO goes to file)
```

## 🚀 Result:

**Claude now sees clean MCP output without false error alerts!**

---

*This critical issue affects ALL MCP servers. Most developers don't know Claude interprets stderr as errors.*