# Security Policy

## Supported versions

| Version | Supported |
| ------- | --------- |
| 1.5.x   | yes       |
| < 1.5   | no        |

Only the latest release line receives fixes. Upgrade to the newest release before reporting.

## Reporting a vulnerability

Please report suspected vulnerabilities **privately**, not through a public issue:

1. Open <https://github.com/D221/convopus/security/advisories/new> ("Report a vulnerability" on the Security tab).
2. Include the version, your operating system, and the smallest set of steps that reproduces it.

You can expect an acknowledgement within a few days. If a fix is needed, a patched release is published to PyPI and a GitHub advisory is issued; credit is given unless you ask otherwise.

## Scope notes

convopus is a command-line wrapper around `ffmpeg`. Reports about the behaviour of `ffmpeg` itself, or about the audio quality of its output, belong upstream to the FFmpeg project. What is in scope here: the CLI, the config parser, output-path handling, and the packaged Windows executable.