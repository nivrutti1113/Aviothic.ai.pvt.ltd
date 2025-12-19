#!/bin/bash
# Generate SBOM using cyclonedx-bom for Python project
pip install cyclonedx-bom
cyclonedx-bom -o sbom.json
echo "SBOM written to sbom.json"