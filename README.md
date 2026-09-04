# Prism

[![C++](https://img.shields.io/badge/C++-23-blue?logo=cplusplus&style=flat-square)](https://isocpp.org/)
[![CMake](https://img.shields.io/badge/CMake-3.20+-064F8C?logo=cmake)](https://cmake.org/)
[![OpenGL](https://img.shields.io/badge/OpenGL-4.6-green?logo=opengl&style=flat-square)](https://www.opengl.org/)
[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&style=flat-square)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue?logo=docker&style=flat-square)](https://www.docker.com/)

> Distributed physically based rendering platform

Prism is an open-source rendering platform that combines a physically based path tracing engine written in C++ with a scalable backend for distributed rendering written in Python.

---

## Repository Structure

```text
prism/
├── backend/                     # Python-based server infrastructure
│   ├── api/                 # REST API endpoints
│   ├── core/                # Core application logic
│   ├── dependencies/        
│   ├── infrastructure/      
│   ├── migrations/          # Database migrations
│   ├── schemas/             # Data validation schemas
│   └── services/            # Business logic services
│
├── renderer/                # C++ path tracing engine
│   ├── include/             # Public headers
│   ├── src/                 # Implementation source files
│   ├── shaders/             # OpenGL shader programs sources
│   ├── lib/                 # Third-party dependencies
│   ├── tests/               # Unit and integration tests
│   └── images/              # Example output renders
│
└── frontend/               
```

---

### Renderer
> Path tracing engine that can run as a standalone CLI application or as a distributed worker.

See the [Renderer documentation](renderer/README.md).

### Backend
> Manages rendering jobs, storage, client communications  and other server-side functionality.

See the [Backend documentation](backend/README.md).
