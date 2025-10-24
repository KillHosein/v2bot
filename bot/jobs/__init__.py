"""Jobs package for scheduled tasks

This package historically tried to import from a module named
`check_expiration.py`. Some installs include a top-level module
`bot/jobs.py` instead of the `bot/jobs/check_expiration.py` file,
which caused imports like `from .jobs import check_expirations` to
fail. To be robust, try the package import first and fall back to
the sibling module if the package-level module is not present.
"""

try:
	# Preferred: package module implementation
	from .check_expiration import check_expirations, backup_and_send_to_admins
except Exception:
	# Fallback: import from the sibling module file `bot/jobs.py`
	# This covers installations where `bot/jobs.py` exists instead of
	# `bot/jobs/check_expiration.py`.
	from .. import jobs as _jobs
	check_expirations = _jobs.check_expirations
	backup_and_send_to_admins = _jobs.backup_and_send_to_admins

__all__ = ['check_expirations', 'backup_and_send_to_admins']
