# Security Policy

## Reporting a vulnerability

Please **do not** open a public issue for security vulnerabilities.

Report privately via
[GitHub Security Advisories](https://github.com/IsaacRop/cutgen/security/advisories/new).
Include what you found, how to reproduce it, and its potential impact.
Expect an initial response within a few days.

## Scope

cutgen orchestrates local processes (`yt-dlp`, `ffmpeg`, `faster-whisper`)
and calls external APIs (Anthropic, YouTube Data/OAuth). Relevant reports
include:

- Command injection in anything that shells out (`ingest`, `render`)
- Path traversal in file writes (`knowledge/niches/<niche>/...`,
  `output/...`)
- Credential handling issues (OAuth token storage/refresh in
  `cutgen_core.publish`)
- Dependency vulnerabilities with a real exploit path in this project

## Never commit real credentials or channel data

This isn't a CVE-style vulnerability, but it's the most likely way this
project actually leaks something sensitive, so it gets its own section:

- **Never commit an API key, OAuth token, or `client_secret.json`.**
  `.gitignore` covers the obvious patterns (`credentials/`, `*token.json`,
  `*client_secret*.json`, `.env*`), but review `git status` and the actual
  diff before pushing — a gitignore pattern is not a guarantee, especially
  if a file was already tracked before the pattern was added.
- **Never commit real channel data**: measured performance numbers,
  discovered patterns, ingested examples, or any content under
  `knowledge/niches/<real-channel>/`. `niches/example-niche/` exists
  specifically so nobody needs to use real data to demonstrate the format.

If you find real credentials or channel data committed anywhere in this
repo's history, report it the same way as a vulnerability — a leaked secret
needs rotation, not just a follow-up commit removing the file (git history
keeps it).

## Supported versions

Pre-1.0, only `main` is supported. There are no tagged releases yet.
