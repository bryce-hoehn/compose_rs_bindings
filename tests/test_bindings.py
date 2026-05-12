import pytest
from compose_spec import PyCompose, PyOptions, parse_duration, format_duration


BASIC_YAML = """
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


@pytest.fixture
def compose():
    return PyCompose.from_yaml(BASIC_YAML)


class TestConstructors:
    def test_from_yaml(self):
        c = PyCompose.from_yaml("services:\n  x:\n    image: alpine\n")
        assert "x" in c

    def test_from_json(self):
        c = PyCompose.from_json('{"services": {"x": {"image": "alpine"}}}')
        assert c.service_names() == ["x"]

    def test_from_dict(self):
        c = PyCompose.from_dict({"services": {"x": {"image": "alpine"}}})
        assert c.service_names() == ["x"]

    def test_from_yaml_invalid(self):
        with pytest.raises(ValueError):
            PyCompose.from_yaml("not: [valid: yaml")

    def test_from_json_invalid(self):
        with pytest.raises(ValueError):
            PyCompose.from_json("{invalid json")

    def test_from_dict_invalid(self):
        with pytest.raises(ValueError):
            PyCompose.from_dict({"services": {"x": {"depends_on": [12345]}}})


class TestSerialization:
    def test_to_yaml(self, compose):
        result = compose.to_yaml()
        assert isinstance(result, str)
        assert "services:" in result
        assert "nginx:latest" in result

    def test_to_json(self, compose):
        result = compose.to_json()
        assert isinstance(result, str)
        import json
        parsed = json.loads(result)
        assert "services" in parsed

    def test_to_dict(self, compose):
        d = compose.to_dict()
        assert isinstance(d, dict)
        assert "services" in d
        assert "web" in d["services"]
        assert d["services"]["web"]["image"] == "nginx:latest"

    def test_roundtrip_yaml(self):
        original = PyCompose.from_yaml(BASIC_YAML)
        yaml_str = original.to_yaml()
        restored = PyCompose.from_yaml(yaml_str)
        assert original == restored

    def test_roundtrip_json(self):
        original = PyCompose.from_yaml(BASIC_YAML)
        json_str = original.to_json()
        restored = PyCompose.from_json(json_str)
        assert original == restored

    def test_roundtrip_dict(self):
        original = PyCompose.from_yaml(BASIC_YAML)
        d = original.to_dict()
        restored = PyCompose.from_dict(d)
        assert original == restored


class TestFieldGetters:
    def test_version(self, compose):
        assert compose.version is None

    def test_name_default_none(self, compose):
        assert compose.name is None

    def test_services(self, compose):
        services = compose.services
        assert isinstance(services, dict)
        assert set(services.keys()) == {"web", "db"}

    def test_networks(self, compose):
        networks = compose.networks
        assert isinstance(networks, dict)
        assert "default" in networks

    def test_volumes(self, compose):
        volumes = compose.volumes
        assert isinstance(volumes, dict)
        assert "db-data" in volumes

    def test_configs_empty(self, compose):
        assert compose.configs == {}

    def test_secrets_empty(self, compose):
        assert compose.secrets == {}

    def test_include_empty(self, compose):
        assert compose.include == []

    def test_extensions_empty(self, compose):
        assert compose.extensions == {}


class TestFieldSetters:
    def test_set_name(self, compose):
        compose.name = "my-project"
        assert compose.name == "my-project"

    def test_set_name_none(self, compose):
        compose.name = "my-project"
        compose.name = None
        assert compose.name is None

    def test_set_version(self, compose):
        compose.version = "3.8"
        assert compose.version == "3.8"

    def test_set_services(self, compose):
        compose.services = {"x": {"image": "alpine"}}
        assert compose.service_names() == ["x"]

    def test_set_networks(self, compose):
        compose.networks = {"frontend": {"driver": "bridge"}}
        assert "frontend" in compose.networks

    def test_set_volumes(self, compose):
        compose.volumes = {"cache": None}
        assert "cache" in compose.volumes


class TestValidation:
    def test_validate_valid(self, compose):
        compose.validate()

    def test_validate_individual(self, compose):
        compose.validate_networks()
        compose.validate_volumes()
        compose.validate_configs()
        compose.validate_secrets()

    def test_validate_missing_network(self):
        c = PyCompose.from_yaml("""
services:
  web:
    image: nginx
    networks:
      - nonexistent
""")
        with pytest.raises(ValueError):
            c.validate()

    def test_validate_missing_volume(self):
        c = PyCompose.from_yaml("""
services:
  web:
    image: nginx
    volumes:
      - shared-vol:/data
  worker:
    image: alpine
    volumes:
      - shared-vol:/data
""")
        with pytest.raises(ValueError):
            c.validate_volumes()


class TestServiceConvenience:
    def test_service_names(self, compose):
        assert compose.service_names() == ["web", "db"]

    def test_get_service(self, compose):
        web = compose.get_service("web")
        assert web is not None
        assert web["image"] == "nginx:latest"

    def test_get_service_missing(self, compose):
        assert compose.get_service("missing") is None

    def test_set_service_new(self, compose):
        compose.set_service("redis", {"image": "redis:7"})
        assert "redis" in compose
        assert compose.get_service("redis")["image"] == "redis:7"

    def test_set_service_replace(self, compose):
        compose.set_service("web", {"image": "nginx:alpine"})
        assert compose.get_service("web")["image"] == "nginx:alpine"

    def test_remove_service(self, compose):
        removed = compose.remove_service("db")
        assert removed is not None
        assert removed["image"] == "postgres:15"
        assert "db" not in compose
        assert len(compose) == 1

    def test_remove_service_missing(self, compose):
        assert compose.remove_service("nonexistent") is None


class TestDunderMethods:
    def test_repr(self, compose):
        assert repr(compose) == "PyCompose(services=2)"

    def test_len(self, compose):
        assert len(compose) == 2

    def test_contains(self, compose):
        assert "web" in compose
        assert "db" in compose
        assert "missing" not in compose

    def test_eq(self):
        a = PyCompose.from_yaml("services:\n  x:\n    image: alpine\n")
        b = PyCompose.from_yaml("services:\n  x:\n    image: alpine\n")
        assert a == b

    def test_ne(self):
        a = PyCompose.from_yaml("services:\n  x:\n    image: alpine\n")
        b = PyCompose.from_yaml("services:\n  y:\n    image: alpine\n")
        assert a != b


class TestPyOptions:
    def test_default(self):
        opts = PyOptions()
        assert opts.apply_merge is False

    def test_constructor(self):
        opts = PyOptions(apply_merge=True)
        assert opts.apply_merge is True

    def test_setter(self):
        opts = PyOptions()
        opts.apply_merge = True
        assert opts.apply_merge is True

    def test_from_yaml(self):
        opts = PyOptions(apply_merge=False)
        c = opts.from_yaml("services:\n  x:\n    image: alpine\n")
        assert "x" in c

    def test_merge_yaml(self):
        yaml = """
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
        c = opts.from_yaml(yaml)
        app_env = c.get_service("app")["environment"]
        assert app_env["LOG_LEVEL"] == "info"
        assert app_env["DEBUG"] == "true"

    def test_no_merge_yaml(self):
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
        opts = PyOptions(apply_merge=False)
        with pytest.raises(ValueError):
            opts.from_yaml(yaml)


class TestParseDuration:
    def test_seconds(self):
        assert parse_duration("30s") == 30.0

    def test_minutes_seconds(self):
        assert parse_duration("1m30s") == 90.0

    def test_hours(self):
        assert parse_duration("2h") == 7200.0

    def test_millis(self):
        assert parse_duration("500ms") == 0.5

    def test_days(self):
        with pytest.raises(ValueError):
            parse_duration("1d")

    def test_invalid(self):
        with pytest.raises(ValueError):
            parse_duration("invalid")

    def test_empty(self):
        with pytest.raises(ValueError):
            parse_duration("")


class TestFormatDuration:
    def test_seconds(self):
        assert format_duration(90.0) == "1m30s"

    def test_hours(self):
        assert format_duration(7200.0) == "2h"

    def test_millis(self):
        result = format_duration(0.5)
        assert "ms" in result

    def test_negative(self):
        with pytest.raises(ValueError):
            format_duration(-1.0)

    def test_nan(self):
        with pytest.raises(ValueError):
            format_duration(float("nan"))

    def test_infinity(self):
        with pytest.raises(ValueError):
            format_duration(float("inf"))
