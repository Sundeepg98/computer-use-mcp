#!/usr/bin/env python3
"""
Docker usage example for computer-use-mcp
Shows how to use the package in Docker containers
"""

import os
import sys
import subprocess
from pathlib import Path


def show_docker_commands():
    """Show Docker commands for using the package"""
    print("=" * 60)
    print("Docker Usage Examples")
    print("=" * 60)
    
    commands = {
        "Build Image": "docker build -t computer-use-mcp .",
        
        "Run Interactive": """docker run -it --rm \\
    -e DISPLAY=$DISPLAY \\
    -v /tmp/.X11-unix:/tmp/.X11-unix \\
    computer-use-mcp""",
        
        "Run with Host Network": """docker run -it --rm \\
    --network host \\
    -e DISPLAY=$DISPLAY \\
    -v /tmp/.X11-unix:/tmp/.X11-unix \\
    computer-use-mcp""",
        
        "Run in Background": """docker run -d \\
    --name computer-use-mcp-server \\
    -p 3333:3333 \\
    computer-use-mcp""",
        
        "Run with Volume Mount": """docker run -it --rm \\
    -v $(pwd)/data:/app/data \\
    -v $(pwd)/screenshots:/app/screenshots \\
    computer-use-mcp""",
        
        "Run with Custom Config": """docker run -it --rm \\
    -v $(pwd)/config.json:/app/config.json \\
    computer-use-mcp --config /app/config.json""",
    }
    
    for description, command in commands.items():
        print(f"\n{description}:")
        print("-" * 40)
        print(f"$ {command}")


def show_docker_compose():
    """Show Docker Compose configuration"""
    print("\n" + "=" * 60)
    print("Docker Compose Configuration")
    print("=" * 60)
    
    compose_yaml = """
version: '3.8'

services:
  computer-use-mcp:
    image: ultrathink/computer-use-mcp:latest
    container_name: computer-use-mcp
    environment:
      - DISPLAY=${DISPLAY}
      - PYTHONUNBUFFERED=1
    volumes:
      - /tmp/.X11-unix:/tmp/.X11-unix:rw
      - ./data:/app/data
      - ./screenshots:/app/screenshots
    network_mode: host
    stdin_open: true
    tty: true
    restart: unless-stopped
    
  # Optional: Run with virtual display
  computer-use-mcp-headless:
    image: ultrathink/computer-use-mcp:latest
    container_name: computer-use-mcp-headless
    environment:
      - DISPLAY=:99
      - PYTHONUNBUFFERED=1
    volumes:
      - ./data:/app/data
    command: |
      sh -c "Xvfb :99 -screen 0 1920x1080x24 &
             python3 /app/src/mcp_server.py"
"""
    
    print("docker-compose.yml:")
    print(compose_yaml)
    
    print("\nUsage:")
    print("$ docker-compose up -d")
    print("$ docker-compose logs -f")
    print("$ docker-compose down")


def show_dockerfile_customization():
    """Show how to customize Dockerfile"""
    print("\n" + "=" * 60)
    print("Dockerfile Customization")
    print("=" * 60)
    
    custom_dockerfile = """
# Custom Dockerfile extending computer-use-mcp
FROM ultrathink/computer-use-mcp:latest

# Add custom dependencies
RUN apt-get update && apt-get install -y \\
    chromium-browser \\
    firefox-esr \\
    && rm -rf /var/lib/apt/lists/*

# Add custom Python packages
RUN pip install selenium webdriver-manager

# Copy custom scripts
COPY custom_scripts/ /app/custom_scripts/

# Set custom environment
ENV CUSTOM_MODE=true
ENV BROWSER=chromium

# Custom entrypoint
ENTRYPOINT ["/app/custom_scripts/entrypoint.sh"]
"""
    
    print("Custom Dockerfile:")
    print(custom_dockerfile)


def show_kubernetes_deployment():
    """Show Kubernetes deployment configuration"""
    print("\n" + "=" * 60)
    print("Kubernetes Deployment")
    print("=" * 60)
    
    k8s_yaml = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: computer-use-mcp
  labels:
    app: computer-use-mcp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: computer-use-mcp
  template:
    metadata:
      labels:
        app: computer-use-mcp
    spec:
      containers:
      - name: computer-use-mcp
        image: ultrathink/computer-use-mcp:latest
        env:
        - name: DISPLAY
          value: ":99"
        - name: PYTHONUNBUFFERED
          value: "1"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        volumeMounts:
        - name: data
          mountPath: /app/data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: computer-use-mcp-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: computer-use-mcp-service
spec:
  selector:
    app: computer-use-mcp
  ports:
    - protocol: TCP
      port: 3333
      targetPort: 3333
"""
    
    print("kubernetes-deployment.yaml:")
    print(k8s_yaml)


def show_development_setup():
    """Show Docker development setup"""
    print("\n" + "=" * 60)
    print("Docker Development Setup")
    print("=" * 60)
    
    print("""
    Development with Docker:
    
    1. Build development image:
       $ docker build -f Dockerfile.dev -t computer-use-mcp:dev .
    
    2. Run with code mounting:
       $ docker run -it --rm \\
           -v $(pwd)/src:/app/src \\
           -v $(pwd)/tests:/app/tests \\
           computer-use-mcp:dev
    
    3. Run tests in container:
       $ docker run --rm computer-use-mcp:dev pytest
    
    4. Interactive development:
       $ docker run -it --rm \\
           -v $(pwd):/app \\
           computer-use-mcp:dev bash
    
    5. Use with docker-compose for development:
       $ docker-compose -f docker-compose.dev.yml up
    """)


def show_ci_integration():
    """Show CI/CD integration with Docker"""
    print("\n" + "=" * 60)
    print("CI/CD Docker Integration")
    print("=" * 60)
    
    github_action = """
name: Docker CI/CD

on:
  push:
    branches: [main]
    tags:
      - 'v*'

jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Login to DockerHub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      
      - name: Build and test
        run: |
          docker build -t test-image .
          docker run --rm test-image pytest
      
      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: |
            ultrathink/computer-use-mcp:latest
            ultrathink/computer-use-mcp:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
"""
    
    print("GitHub Actions Docker CI/CD:")
    print(github_action)


def main():
    """Run all Docker examples"""
    show_docker_commands()
    show_docker_compose()
    show_dockerfile_customization()
    show_kubernetes_deployment()
    show_development_setup()
    show_ci_integration()
    
    print("\n" + "=" * 60)
    print("✅ Docker Usage Examples Completed!")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())