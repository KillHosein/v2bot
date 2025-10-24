"""Jobs package for scheduled tasks

This package historically tried to import from a module named
`check_expiration.py`. Some installs include a top-level module
`bot/jobs.py` instead of the `bot/jobs/check_expiration.py` file,
which caused imports like `from .jobs import check_expirations` to
fail. To be robust, try the package import first and fall back to
the sibling module if the package-level module is not present.
"""

def _load_jobs_functions():
    """Return the jobs callables, preferring the package implementation."""

    try:
        # Preferred: package module implementation
        from .check_expiration import check_expirations, backup_and_send_to_admins  # type: ignore
    except ModuleNotFoundError as exc:
        # Only fall back when *this* module is missing; otherwise, bubble up the error.
        if getattr(exc, "name", None) not in {__name__ + ".check_expiration", "bot.jobs.check_expiration"}:
            raise

        # Fallback: import from the legacy sibling module file `bot/jobs.py`.
        # Importing `bot.jobs` directly would recurse into this package while it
        # is still being initialised which results in a partially initialised
        # module. Instead, load the legacy module under a distinct name using
        # importlib so we can safely access its attributes.
        import importlib.util
        import sys
        from pathlib import Path

        module_name = "bot._legacy_jobs"
        legacy_jobs = sys.modules.get(module_name)
        if legacy_jobs is None:
            _pkg_dir = Path(__file__).resolve().parent
            _legacy_path = _pkg_dir.parent / "jobs.py"

            spec = importlib.util.spec_from_file_location(module_name, _legacy_path)
            if spec is None or spec.loader is None:
                raise ImportError("Unable to load legacy jobs module") from exc

            legacy_jobs = importlib.util.module_from_spec(spec)
            # Ensure relative imports like ``from .config`` keep working when the
            # legacy module is executed outside of the package machinery.
            legacy_jobs.__package__ = "bot"
            legacy_jobs.__loader__ = spec.loader

            sys.modules[module_name] = legacy_jobs
            spec.loader.exec_module(legacy_jobs)

        try:
            return legacy_jobs.check_expirations, legacy_jobs.backup_and_send_to_admins
        except AttributeError as attr_err:
            raise ImportError(
                "Legacy jobs module is missing required callables"
            ) from attr_err
    else:
        return check_expirations, backup_and_send_to_admins


check_expirations, backup_and_send_to_admins = _load_jobs_functions()
del _load_jobs_functions

__all__ = ['check_expirations', 'backup_and_send_to_admins']
