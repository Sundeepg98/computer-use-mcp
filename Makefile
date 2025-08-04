# MCP Development Makefile

.PHONY: help install test run shell clean

help:
	@echo "MCP Development Commands:"
	@echo "  make install  - Install package in development mode"
	@echo "  make test     - Run tests"  
	@echo "  make run      - Start MCP server"
	@echo "  make shell    - Open Python shell with MCP loaded"
	@echo "  make clean    - Clean build artifacts"

install:
	pip install -e ".[dev]"

test:
	python -m pytest tests/ -v

run:
	python -m mcp.mcp_server

shell:
	./dev.py shell

clean:
	./dev.py clean

# Shortcuts
t: test
r: run
s: shell
