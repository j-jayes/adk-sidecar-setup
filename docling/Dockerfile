# Docling sidecar – pre-built CPU image (no custom build needed).
# Using the quay.io image directly in docker-compose.yml.
# This Dockerfile is kept as a placeholder for future customisation
# (e.g. adding LibreOffice for DOCX support, custom OCR engines, etc.).

FROM quay.io/docling-project/docling-serve-cpu:latest

USER root

# Example: install LibreOffice for full DOCX/PPTX support
# RUN dnf install -y libreoffice-writer libreoffice-calc libreoffice-core \
#     liberation-fonts && dnf clean all && rm -rf /var/cache/dnf/*

USER 1001
