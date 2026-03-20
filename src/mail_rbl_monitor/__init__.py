from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("mail-rbl-monitor")
except PackageNotFoundError:  # pragma: no cover - fallback for editable local execution
    __version__ = "0.1.0"

__all__ = ["__version__"]
