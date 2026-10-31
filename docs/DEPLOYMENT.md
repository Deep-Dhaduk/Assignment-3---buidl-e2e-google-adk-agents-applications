# Deployment and operational boundaries

## Supported local environment

The verified path uses Python, Node, Gemini API access, local SQLite and MCP subprocesses. Google Cloud billing is not required for this path. The custom CLI/API persists sessions in a SQLite file. Keep the API on localhost unless you add a trusted reverse proxy and appropriate transport security.

`APP_API_KEY` authenticates one operator. Do not treat it as a multi-customer identity system. Production hosting needs per-user authentication and authorization, secret management, a persistent/shared session backend, durable artifact storage, rate quotas, and operational monitoring.

## Docker application package (requires Docker; not locally verified here)

Set `GOOGLE_API_KEY` and `APP_API_KEY` in `.env`, then:

```bash
docker compose up --build
```

The API listens at `http://127.0.0.1:8080/docs`. Named volumes retain local data and artifacts. The image uses a non-root user. Compose deliberately leaves review execution disabled; no host Docker socket is mounted.

## Isolated review tests

On a development machine with Docker:

```bash
docker build -f deployment/review-runner.Dockerfile -t assignment-review-runner:local .
```

Set `REVIEW_EXECUTION=docker` and run the review through the host Python application. The launcher mounts only a registered sample project read-only and applies no-network, CPU/memory/process limits and dropped capabilities. It removes a timed-out container. Host `trusted` mode is only for repository fixtures and does not provide this isolation.

Do not enable general uploaded-code execution in the API without a dedicated worker isolation system. Cloud Run does not provide the host Docker daemon assumed by this local runner.

## PostgreSQL / AlloyDB data backend

The business schema uses portable SQLAlchemy tables and a psycopg driver. Set:

```text
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE
```

Then run `python -m assignment init` once against the target database. `initialize` creates tables and inserts missing seed rows without resetting stock or orders. Schema upgrades need explicit migrations; startup `create_all` is not a migration system.

For AlloyDB, provision an instance and database, configure network access and authentication, and use its reachable PostgreSQL connection endpoint. Do not copy example passwords from tutorials. This repository's PostgreSQL/AlloyDB path has not been exercised in the current environment. SQLite concurrency tests are not evidence of AlloyDB deployment.

The implementation uses a custom MCP server for catalog tools. It does not deploy MCP Toolbox for Databases. The reference codelab's Toolbox configuration and managed infrastructure are a separate integration path: [official sports-shop codelab](https://codelabs.developers.google.com/codelabs/sports-agent-adk-mcp-alloydb?hl=en).

## Cloud Run preparation (optional, not performed)

1. Obtain a Google Cloud project with billing and enable the services required by your chosen deployment.
2. Build the Dockerfile and publish the image to Artifact Registry.
3. Configure Gemini access through a managed secret or Vertex AI with a narrowly scoped service account.
4. Configure the application API secret. Keep Cloud Run authentication enabled; the application secret alone is not a complete production identity system.
5. Connect the business database through appropriate private networking/connector configuration.
6. Replace the local SQLite session store with a shared session service before running multiple instances. Store artifacts durably rather than relying on the container filesystem.
7. Configure resource limits, logs, request timeouts, budget alerts, and cleanup. Run smoke tests against the deployed service.

The Dockerfile binds port 8080. The current API uses one worker and serializes runs; it is intended for a controlled demonstration. The repository is not marked cloud-deployed, and no hosting charges have been incurred by this implementation work.

## Repository hygiene

`.env`, databases, virtual environments, npm modules and local traces are ignored. Do not include keys, service-account files or raw customer data in screenshots, videos or commits. Review generated evidence before copying it to a tracked artifact directory.
