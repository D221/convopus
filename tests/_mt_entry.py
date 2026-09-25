"""Subprocess entry point for the multiprocessing integration test.

Patches the appdirs config resolver to an isolated directory passed via
the CONVOPUS_TEST_CONFIG_DIR environment variable, then runs the CLI.
Multiprocessing spawn re-imports this file in worker processes (as
__mp_main__), so main() must stay behind the __main__ guard.
"""

import os

import convopus.config

convopus.config.user_config_dir = lambda app_name, app_author: os.environ[  # noqa: E402
    "CONVOPUS_TEST_CONFIG_DIR"
]

from convopus.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
