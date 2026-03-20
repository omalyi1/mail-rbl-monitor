from __future__ import annotations

from collections.abc import Sequence
from ipaddress import IPv4Address

from mail_rbl_monitor.domain.exceptions import ProviderResolutionError
from mail_rbl_monitor.domain.ports import DnsResolverPort


class StubDnsResolver(DnsResolverPort):
    def resolve_a(self, query_name: str, timeout_seconds: int) -> Sequence[IPv4Address]:
        raise ProviderResolutionError(
            "DNS resolution is not implemented in Phase 1. "
            f"Received query_name={query_name!r} timeout_seconds={timeout_seconds}."
        )
