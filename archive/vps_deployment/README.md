# VPS Deployment Archive

**Archived:** October 28, 2025  
**Reason:** Using Modal Labs instead of VPS deployment

## Contents

- `DEPLOY_TO_VPS.md` - VPS deployment instructions
- `create_deployment.sh` - Deployment automation script
- `.deployignore` - Files to exclude from deployment

## Why Archived

**Original Plan:** Deploy ClipScribe to a VPS for self-hosted processing

**Current Approach:** Modal Labs serverless GPU
- No server management
- Auto-scaling
- Pay-per-use
- GPU access (A10G)
- 11.6x realtime processing

**Decision:** Modal is superior for MVP/product (no ops burden, better economics)

## Future Use

May be useful if:
- Customer requests self-hosted deployment
- Air-gapped system requirements
- Regulatory requirements for data locality

Can retrieve from archive if needed.

