# Deployment

See [README.md](README.md#container-deployment) for Docker, persistent volumes, CORS and remote Qdrant configuration. The previous Vercel-only API instructions are superseded. Use a persistent container for the API and host the frontend build separately. Public deployments need gateway authentication, request limits and provider budgets.
