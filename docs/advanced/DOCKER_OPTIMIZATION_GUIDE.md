# Docker Optimization Guide

*Last Updated: 2025-08-26*

## Overview

ClipScribe's `Dockerfile` is optimized to produce small, efficient, and secure container images. This is achieved through two primary strategies: multi-stage builds and an optional dependency system.

## Multi-Stage Builds

Our `Dockerfile` uses a multi-stage build to separate the build environment from the final runtime environment.

-   **`builder` stage**: This stage installs all the necessary build tools and dependencies (like Poetry) to create a clean Python virtual environment.
-   **`base` stage**: This stage takes the virtual environment from the `builder` stage and adds the necessary runtime dependencies, creating a common foundation for our final images.
-   **Final stages (`api`, `web`, `cli`)**: These stages start from the `base` image and add only the application code necessary for that specific service.

This approach results in significantly smaller final images, as the build tools and intermediate artifacts are not included in the production containers.

## Optional Dependency System

ClipScribe uses Poetry's optional dependency groups to allow for flexible installations. This means you only need to install the libraries required for the features you intend to use, which helps to keep the runtime environment lean.

The primary dependency groups are defined in `pyproject.toml` and include `api` and `web`. Our multi-stage `Dockerfile` correctly installs all necessary production dependencies for each service.
