"""Repositories: the only layer allowed to talk to the database.

Rules of the three-layer architecture:
- a blueprint (app/blueprints/) is an HTTP controller: it reads the
  request, validates the body, calls a service and shapes the response;
- a service (app/services/) holds business rules and orchestration; it
  never touches request, g or HTTP responses;
- a repository (app/repositories/) owns the SQL and row mapping; it
  contains no business rules.

Each repository is a class, exposed as a single module-level instance
(e.g. `agent_repository = AgentRepository()`): easy to import, easy to
mock in tests, no framework magic.
"""
