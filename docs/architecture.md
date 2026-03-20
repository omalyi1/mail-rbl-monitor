# Architecture

## Why a one-shot CLI

This service is designed as a deterministic one-shot command instead of a long-running worker. That keeps execution simple, makes failures easy to reason about, and pairs naturally with `cron` or `systemd` timers. The application starts, validates configuration, performs its work, emits logs, and exits.

That shape is a better fit than an in-process scheduler for an early monitoring utility because it reduces runtime state, avoids extra infrastructure, and keeps deployments easy to operate.

## Layered boundaries

The repository uses a small layered architecture:

- `domain/`: pure business vocabulary, value objects, enums, exceptions, and ports
- `application/`: one-shot orchestration for the check workflow
- `infrastructure/`: adapters for DNS resolution and notification delivery
- `presentation/`: reserved for future user-facing surfaces without leaking them into the core
- `cli.py`: process entrypoint and argument parsing

The domain layer does not know about logging configuration, shell invocation, or environment parsing. Infrastructure adapters sit behind ports so later DNSBL and notifier implementations remain testable.

## Configuration flow

Configuration enters through `mail_rbl_monitor.config.Settings`, which reads environment variables and optional `.env` values using `pydantic-settings`.

The settings layer is responsible for:

- parsing comma-separated IPv4 targets and DNSBL provider names
- validating timeout bounds
- enforcing notifier credential requirements only when a notifier is enabled
- converting validated settings into a domain-facing runtime summary

Secrets are never logged. The runtime summary only includes safe operational context such as counts, enabled channels, and configured targets/providers.

## Extensibility path

Phase 1 intentionally stops at bootstrap behavior, but the structure is ready for the next steps:

- add provider-specific DNSBL query composition and response parsing under `infrastructure/providers/`
- implement a real DNS resolver adapter behind `DnsResolverPort`
- add Telegram and Discord notifier adapters behind `NotificationSenderPort`
- introduce state only if a concrete deduplication or audit requirement appears

The repository is intentionally not shaped as a generic monitoring platform. It is a focused mail reputation check service with deterministic execution.
