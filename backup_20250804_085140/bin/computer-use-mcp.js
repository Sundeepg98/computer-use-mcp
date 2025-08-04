#!/usr/bin/env node
const { spawn } = require('child_process');
const path = require('path');

// Find Python executable
const python = process.platform === 'win32' ? 'python' : 'python3';

// Path to MCP server
const serverPath = path.join(__dirname, '..', 'src', 'mcp_server.py');

// Spawn Python process
const proc = spawn(python, [serverPath], {
  stdio: 'inherit',
  env: process.env
});

proc.on('error', (err) => {
  console.error('Failed to start MCP server:', err);
  process.exit(1);
});

proc.on('exit', (code) => {
  process.exit(code);
});