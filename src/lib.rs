use compose_spec_crate::{Compose, Identifier, Options};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::time::Duration;

fn to_py_err(e: impl std::fmt::Display) -> PyErr {
    PyValueError::new_err(e.to_string())
}

fn to_py_obj<'py, T: serde::Serialize>(
    py: Python<'py>,
    val: &T,
) -> PyResult<Bound<'py, PyAny>> {
    let json_str = serde_json::to_string(val).map_err(to_py_err)?;
    py.import("json")?.call_method1("loads", (json_str,))
}

fn from_py_obj<T: serde::de::DeserializeOwned>(obj: Bound<'_, PyAny>) -> PyResult<T> {
    let json_mod = obj.py().import("json")?;
    let json_str: String = json_mod.call_method1("dumps", (obj,))?.extract()?;
    serde_json::from_str(&json_str).map_err(to_py_err)
}

#[pyclass(skip_from_py_object)]
#[derive(Clone)]
pub struct PyCompose {
    inner: Compose,
}

#[pymethods]
impl PyCompose {
    // ── Constructors ──────────────────────────────

    #[staticmethod]
    fn from_yaml(yaml: &str) -> PyResult<Self> {
        let inner = serde_yaml::from_str(yaml).map_err(to_py_err)?;
        Ok(Self { inner })
    }

    #[staticmethod]
    fn from_json(json: &str) -> PyResult<Self> {
        let inner = serde_json::from_str(json).map_err(to_py_err)?;
        Ok(Self { inner })
    }

    #[staticmethod]
    fn from_dict(dict: Bound<'_, PyDict>) -> PyResult<Self> {
        let inner: Compose = from_py_obj(dict.into_any())?;
        Ok(Self { inner })
    }

    // ── Serialization ─────────────────────────────

    fn to_yaml(&self) -> PyResult<String> {
        serde_yaml::to_string(&self.inner).map_err(to_py_err)
    }

    fn to_json(&self) -> PyResult<String> {
        serde_json::to_string(&self.inner).map_err(to_py_err)
    }

    fn to_dict<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        to_py_obj(py, &self.inner)
    }

    // ── Field getters ─────────────────────────────

    #[getter]
    fn version<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        to_py_obj(py, &self.inner.version)
    }

    #[getter]
    fn name<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        to_py_obj(py, &self.inner.name)
    }

    #[getter]
    fn services<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        to_py_obj(py, &self.inner.services)
    }

    #[getter]
    fn networks<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        to_py_obj(py, &self.inner.networks)
    }

    #[getter]
    fn volumes<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        to_py_obj(py, &self.inner.volumes)
    }

    #[getter]
    fn configs<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        to_py_obj(py, &self.inner.configs)
    }

    #[getter]
    fn secrets<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        to_py_obj(py, &self.inner.secrets)
    }

    #[getter]
    fn include<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        to_py_obj(py, &self.inner.include)
    }

    #[getter]
    fn extensions<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        to_py_obj(py, &self.inner.extensions)
    }

    // ── Field setters ─────────────────────────────

    #[setter]
    fn set_version(&mut self, value: Bound<'_, PyAny>) -> PyResult<()> {
        self.inner.version = from_py_obj(value)?;
        Ok(())
    }

    #[setter]
    fn set_name(&mut self, value: Bound<'_, PyAny>) -> PyResult<()> {
        self.inner.name = from_py_obj(value)?;
        Ok(())
    }

    #[setter]
    fn set_services(&mut self, value: Bound<'_, PyAny>) -> PyResult<()> {
        self.inner.services = from_py_obj(value)?;
        Ok(())
    }

    #[setter]
    fn set_networks(&mut self, value: Bound<'_, PyAny>) -> PyResult<()> {
        self.inner.networks = from_py_obj(value)?;
        Ok(())
    }

    #[setter]
    fn set_volumes(&mut self, value: Bound<'_, PyAny>) -> PyResult<()> {
        self.inner.volumes = from_py_obj(value)?;
        Ok(())
    }

    #[setter]
    fn set_configs(&mut self, value: Bound<'_, PyAny>) -> PyResult<()> {
        self.inner.configs = from_py_obj(value)?;
        Ok(())
    }

    #[setter]
    fn set_secrets(&mut self, value: Bound<'_, PyAny>) -> PyResult<()> {
        self.inner.secrets = from_py_obj(value)?;
        Ok(())
    }

    #[setter]
    fn set_include(&mut self, value: Bound<'_, PyAny>) -> PyResult<()> {
        self.inner.include = from_py_obj(value)?;
        Ok(())
    }

    #[setter]
    fn set_extensions(&mut self, value: Bound<'_, PyAny>) -> PyResult<()> {
        self.inner.extensions = from_py_obj(value)?;
        Ok(())
    }

    // ── Validation ────────────────────────────────

    fn validate(&self) -> PyResult<()> {
        self.inner.validate_all().map_err(to_py_err)
    }

    fn validate_networks(&self) -> PyResult<()> {
        self.inner.validate_networks().map_err(to_py_err)
    }

    fn validate_volumes(&self) -> PyResult<()> {
        self.inner.validate_volumes().map_err(to_py_err)
    }

    fn validate_configs(&self) -> PyResult<()> {
        self.inner.validate_configs().map_err(to_py_err)
    }

    fn validate_secrets(&self) -> PyResult<()> {
        self.inner.validate_secrets().map_err(to_py_err)
    }

    // ── Service convenience ───────────────────────

    fn service_names(&self) -> Vec<String> {
        self.inner
            .services
            .keys()
            .map(|id| id.to_string())
            .collect()
    }

    fn get_service<'py>(
        &self,
        py: Python<'py>,
        name: &str,
    ) -> PyResult<Option<Bound<'py, PyAny>>> {
        let id = name.parse::<Identifier>().map_err(to_py_err)?;
        match self.inner.services.get(&id) {
            Some(svc) => to_py_obj(py, svc).map(Some),
            None => Ok(None),
        }
    }

    fn set_service(&mut self, name: &str, service: Bound<'_, PyAny>) -> PyResult<()> {
        let id = name.parse::<Identifier>().map_err(to_py_err)?;
        let svc = from_py_obj(service)?;
        self.inner.services.insert(id, svc);
        Ok(())
    }

    fn remove_service<'py>(
        &mut self,
        py: Python<'py>,
        name: &str,
    ) -> PyResult<Option<Bound<'py, PyAny>>> {
        let id = name.parse::<Identifier>().map_err(to_py_err)?;
        match self.inner.services.shift_remove(&id) {
            Some(svc) => to_py_obj(py, &svc).map(Some),
            None => Ok(None),
        }
    }

    // ── Dunder methods ────────────────────────────

    fn __repr__(&self) -> String {
        format!("PyCompose(services={})", self.inner.services.len())
    }

    fn __len__(&self) -> usize {
        self.inner.services.len()
    }

    fn __contains__(&self, name: &str) -> PyResult<bool> {
        match name.parse::<Identifier>() {
            Ok(id) => Ok(self.inner.services.contains_key(&id)),
            Err(_) => Ok(false),
        }
    }

    fn __eq__(&self, other: &Self) -> bool {
        self.inner == other.inner
    }
}

#[pyclass(skip_from_py_object)]
pub struct PyOptions {
    apply_merge_val: bool,
}

#[pymethods]
impl PyOptions {
    #[new]
    #[pyo3(signature = (apply_merge=false))]
    fn new(apply_merge: bool) -> Self {
        Self { apply_merge_val: apply_merge }
    }

    #[getter]
    fn apply_merge(&self) -> bool {
        self.apply_merge_val
    }

    #[setter]
    fn set_apply_merge(&mut self, val: bool) {
        self.apply_merge_val = val;
    }

    fn from_yaml(&self, yaml: &str) -> PyResult<PyCompose> {
        let mut opts = Options::default();
        opts.apply_merge(self.apply_merge_val);
        let inner = opts.from_yaml_str(yaml).map_err(to_py_err)?;
        Ok(PyCompose { inner })
    }
}

#[pyfunction]
pub fn parse_duration(s: &str) -> PyResult<f64> {
    compose_spec_crate::duration::parse(s)
        .map(|d| d.as_secs_f64())
        .map_err(to_py_err)
}

#[pyfunction]
pub fn format_duration(secs: f64) -> PyResult<String> {
    let dur = Duration::try_from_secs_f64(secs).map_err(to_py_err)?;
    Ok(compose_spec_crate::duration::to_string(dur))
}

#[pymodule]
pub mod compose_spec {
    #[pymodule_export]
    pub use super::{PyCompose, PyOptions, parse_duration, format_duration};
}
