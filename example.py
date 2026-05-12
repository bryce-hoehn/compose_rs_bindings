"""
Examples demonstrating the compose_rs_bindings Python API.

Install: pip install .
Build:   maturin develop
"""
from compose_rs_bindings import PyCompose, PyOptions, parse_duration, format_duration


# ── 1. Parse a Compose file from YAML ────────────

yaml = """
services:
  web:
    image: nginx:latest
    ports:
      - 80:80
      - 443:443
    environment:
      FOO: bar
  db:
    image: postgres:15
    volumes:
      - db-data:/var/lib/postgresql/data
volumes:
  db-data:
networks:
  default:
    driver: bridge
"""

c = PyCompose.from_yaml(yaml)
print(f"Parsed: {c}")


# ── 2. Read and modify top-level fields ──────────

print(f"Service names: {c.service_names()}")
print(f"Networks: {c.networks}")
print(f"Volumes: {c.volumes}")

# Set the project name
c.name = "my-project"
print(f"Name: {c.name}")


# ── 3. Work with individual services ─────────────

# Get a service as a dict
web = c.get_service("web")
print(f"Web image: {web['image']}")

# Modify and set it back
web["image"] = "nginx:alpine"
web["environment"]["BAZ"] = "qux"
c.set_service("web", web)
print(f"Updated web: {c.get_service('web')}")

# Add a new service
c.set_service("redis", {"image": "redis:7", "ports": ["6379:6379"]})
print(f"After adding redis: {c.service_names()}")

# Remove a service
removed = c.remove_service("redis")
print(f"Removed: {removed}")

# Check membership
print(f"'web' in compose: {'web' in c}")
print(f"len(compose): {len(c)}")


# ── 4. Serialize to different formats ────────────

# Back to YAML
yaml_out = c.to_yaml()

# To JSON string
json_out = c.to_json()

# To Python dict
d = c.to_dict()
print(f"Dict keys: {list(d.keys())}")

# Parse from dict
c2 = PyCompose.from_dict({"services": {"api": {"image": "fastapi:latest"}}})

# Parse from JSON
c3 = PyCompose.from_json('{"services": {"worker": {"image": "celery:latest"}}}')


# ── 5. Validation ────────────────────────────────

# Check that all resource references are valid
c.validate()

# Individual checks
c.validate_networks()
c.validate_volumes()
c.validate_configs()
c.validate_secrets()
print("Validation passed")


# ── 6. YAML merge keys (<<) with PyOptions ───────

yaml_with_merge = """
services:
  base:
    environment: &defaults
      LOG_LEVEL: info
      DEBUG: "false"
  app:
    environment:
      <<: *defaults
      DEBUG: "true"
"""

opts = PyOptions(apply_merge=True)
c4 = opts.from_yaml(yaml_with_merge)
app_env = c4.get_service("app")["environment"]
print(f"Merged environment: {app_env}")


# ── 7. Duration utilities ────────────────────────

seconds = parse_duration("1m30s")
print(f"1m30s = {seconds}s")

formatted = format_duration(90.0)
print(f"90s = {formatted}")

seconds = parse_duration("2h")
print(f"2h = {seconds}s")


# ── 8. Equality ──────────────────────────────────

a = PyCompose.from_yaml("services:\n  x:\n    image: alpine\n")
b = PyCompose.from_yaml("services:\n  x:\n    image: alpine\n")
print(f"Equal compose files: {a == b}")
