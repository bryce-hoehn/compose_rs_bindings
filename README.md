# compose-spec

Python bindings for the [compose_spec](https://docs.rs/compose_spec/latest/compose_spec/) Rust library — a fully validated, spec-compliant Docker Compose file parser and serializer.

## Installation

```bash
pip install compose-spec
```

For development:

```bash
pip install maturin
maturin develop --release
```

Requires Rust toolchain (`rustup`) and Python >= 3.8.

## Quick Start

```python
from compose_spec import PyCompose

yaml = """
services:
  web:
    image: nginx:latest
    ports:
      - 80:80
    environment:
      FOO: bar
volumes:
  data:
"""

c = PyCompose.from_yaml(yaml)
print(c.service_names())  # ['web']
print(c.volumes)          # {'data': None}

# Round-trip back to YAML
print(c.to_yaml())

# Convert to Python dict
d = c.to_dict()
```

## API Reference

### `PyCompose`

The main class representing a parsed Docker Compose file.

#### Constructors

| Method | Description |
|--------|-------------|
| `PyCompose.from_yaml(yaml_str)` | Parse from a YAML string |
| `PyCompose.from_json(json_str)` | Parse from a JSON string |
| `PyCompose.from_dict(d)` | Parse from a Python dict |

All constructors raise `ValueError` on invalid input.

#### Serialization

| Method | Returns | Description |
|--------|---------|-------------|
| `to_yaml()` | `str` | Serialize to YAML |
| `to_json()` | `str` | Serialize to JSON |
| `to_dict()` | `dict` | Serialize to a Python dict |

#### Properties (getters and setters)

All top-level Compose fields are exposed as Python properties. Getting a property returns a native Python object (dict, list, str, or None). Setting a property accepts the same types.

| Property | Type | Description |
|----------|------|-------------|
| `name` | `str \| None` | Project name |
| `version` | `str \| None` | Compose file version (legacy) |
| `services` | `dict` | Service definitions |
| `networks` | `dict` | Network definitions |
| `volumes` | `dict` | Volume definitions |
| `configs` | `dict` | Config definitions |
| `secrets` | `dict` | Secret definitions |
| `include` | `list` | Included sub-projects |
| `extensions` | `dict` | Extension values (`x-*` keys) |

```python
c.name = "my-project"
print(c.services)        # {'web': {'image': 'nginx:latest', ...}}
c.networks = {"frontend": {"driver": "bridge"}}
```

#### Validation

Checks that all resource references (networks, volumes, configs, secrets) used in services are defined at the top level. Raises `ValueError` with a descriptive message if validation fails.

| Method | Description |
|--------|-------------|
| `validate()` | Run all validation checks |
| `validate_networks()` | Check network references |
| `validate_volumes()` | Check volume references |
| `validate_configs()` | Check config references |
| `validate_secrets()` | Check secret references |

```python
c = PyCompose.from_yaml("""
services:
  web:
    image: nginx
    networks:
      - missing_net
""")
try:
    c.validate()
except ValueError as e:
    print(e)  # network "missing_net" is not defined
```

#### Service convenience methods

| Method | Returns | Description |
|--------|---------|-------------|
| `service_names()` | `list[str]` | All service names in order |
| `get_service(name)` | `dict \| None` | Get a single service by name |
| `set_service(name, service_dict)` | `None` | Add or replace a service |
| `remove_service(name)` | `dict \| None` | Remove and return a service |

```python
web = c.get_service("web")
web["image"] = "nginx:alpine"
c.set_service("web", web)

c.set_service("redis", {"image": "redis:7"})
removed = c.remove_service("redis")
```

#### Dunder methods

| Expression | Description |
|------------|-------------|
| `len(c)` | Number of services |
| `"web" in c` | Check if a service exists |
| `c1 == c2` | Structural equality |
| `repr(c)` | String representation |

---

### `PyOptions`

Options builder for controlling YAML parsing behavior.

```python
from compose_spec import PyOptions

opts = PyOptions(apply_merge=True)
# or:
opts = PyOptions()
opts.apply_merge = True

c = opts.from_yaml(yaml_string)
```

#### Constructor

```python
PyOptions(apply_merge=False)
```

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `apply_merge` | `bool` | `False` | Whether to merge YAML `<<` keys |

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `from_yaml(yaml_str)` | `PyCompose` | Parse YAML with the configured options |

**When to use `apply_merge`:** If your Compose file uses YAML anchors and the merge key (`<<`) to share configuration between services, set `apply_merge=True` to resolve them during parsing.

```python
yaml = """
services:
  base:
    environment: &defaults
      LOG_LEVEL: info
  app:
    environment:
      <<: *defaults
      LOG_LEVEL: debug
"""

opts = PyOptions(apply_merge=True)
c = opts.from_yaml(yaml)
# app.environment is now {"LOG_LEVEL": "debug"} (merged from base)
```

---

### `parse_duration(s)`

Parse a Compose-format duration string into seconds.

```python
from compose_spec import parse_duration

parse_duration("1m30s")   # 90.0
parse_duration("2h")      # 7200.0
parse_duration("500ms")   # 0.5
```

**Supported units:** `ns`, `us`, `ms`, `s`, `m`, `h`

Raises `ValueError` for invalid format.

---

### `format_duration(secs)`

Format a number of seconds as a Compose duration string.

```python
from compose_spec import format_duration

format_duration(90.0)    # "1m30s"
format_duration(7200.0)  # "2h"
format_duration(0.5)     # "500ms"
```

Raises `ValueError` for negative values, NaN, or infinity.

---

## How It Works

This library wraps the Rust [compose_spec](https://crates.io/crates/compose_spec) crate using [PyO3](https://pyo3.rs/). Parsing and validation happen in Rust, giving you:

- **Full Compose spec compliance** — every field validated against the spec
- **Round-trip fidelity** — parse YAML, modify in Python, serialize back without data loss
- **Fast parsing** — Rust-powered YAML/JSON deserialization

Python objects are converted via a JSON roundtrip: Rust structs serialize to JSON, then Python's `json.loads` produces native dicts/lists/strings. This keeps the binding layer thin while giving you full access to the data tree.

## Building from Source

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install maturin
pip install maturin

# Build and install in development mode
maturin develop

# Run the examples
python example.py
```

## License

See [LICENSE](LICENSE).
