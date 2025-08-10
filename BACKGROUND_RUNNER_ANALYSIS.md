# Background Runner Analysis for Lite v2.1.0

## What is mcp-bgtask?
The [mcp-bgtask](https://github.com/nanoseil/mcp-bgtask) is a separate MCP server that provides:
- Running background commands (dev servers, builds, etc.)
- Managing long-running processes
- Starting/stopping/listing background tasks
- Interactive stdin/stdout communication
- Process cleanup on shutdown

## Should We Add This to Lite?

### Current Lite v2.1.0 Focus
Our Lite version focuses on **desktop automation**:
- Screenshot, click, type, scroll, etc.
- Quick, synchronous actions
- Safety-first approach
- Clean, maintainable code

### Background Tasks Are Different
Background task management is a **separate concern**:
- Long-running processes
- Process lifecycle management
- Stream handling (stdout/stderr)
- Signal handling
- Different security considerations

## Recommendation: Keep Them Separate

### Why?
1. **Single Responsibility**: Lite does desktop automation, bg-runner does process management
2. **Modularity**: Users can choose what they need
3. **Complexity**: Adding bg tasks would complicate Lite
4. **Security**: Different security models (UI automation vs process execution)
5. **Maintenance**: Easier to maintain focused tools

### The Unix Philosophy
> "Do one thing and do it well"

- **computer-use-lite**: Desktop automation
- **mcp-bgtask**: Background process management
- **Other MCP servers**: Other specialized tasks

## How They Work Together

Users can run multiple MCP servers simultaneously:
```json
{
  "mcpServers": {
    "computer-use-lite": {
      "command": "python3 /path/to/lite/start_mcp_server.py"
    },
    "bg-runner": {
      "command": "npx @nanoseil/mcp-bgtask"
    }
  }
}
```

## Example Use Cases

### With Both Servers:
1. Use `bg-runner` to start a dev server
2. Use `computer-use-lite` to interact with the UI
3. Use `bg-runner` to monitor logs
4. Use `computer-use-lite` to test UI changes

### Lite Only:
- UI automation
- Screenshot capture
- Form filling
- Testing interactions

### bg-runner Only:
- Running builds
- Starting servers
- Background monitoring
- Log collection

## Conclusion

**Don't add background runner to Lite.**

Instead:
1. Keep Lite focused on desktop automation
2. Recommend mcp-bgtask for background tasks
3. Document how to use them together
4. Maintain clear separation of concerns

This keeps both tools:
- Simple
- Maintainable
- Secure
- Focused

Users who need background tasks can add mcp-bgtask. Users who only need desktop automation get a clean, simple tool.

## If You Really Want Background Support

If background task support is essential, consider:
1. Creating a separate `computer-use-bg` package
2. Adding it as an optional extension
3. Making it a plugin system

But **don't** add it to the core Lite package - it goes against the "lite" philosophy.