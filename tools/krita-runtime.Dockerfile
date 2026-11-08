FROM debian:unstable-slim@sha256:0616b6687a2b155010c25f9019d2e87461bed2b19b2733ca079b4700a2513949
RUN apt-get update && apt-get install -y --no-install-recommends krita xvfb xauth python3 && rm -rf /var/lib/apt/lists/*
ENV PYTHONDONTWRITEBYTECODE=1 QT_QPA_PLATFORM=xcb XDG_CONFIG_HOME=/tmp/config XDG_CACHE_HOME=/tmp/cache XDG_DATA_HOME=/tmp/data
RUN apt-get update && apt-get install -y --no-install-recommends python3-pyqt5 && rm -rf /var/lib/apt/lists/*
