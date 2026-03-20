import pytest

from mail_rbl_monitor.domain.exceptions import ConfigurationError
from mail_rbl_monitor.domain.models import DnsblProvider, TargetIP


def test_target_ip_from_raw_accepts_ipv4_string() -> None:
    target_ip = TargetIP.from_raw("136.243.71.222")

    assert str(target_ip) == "136.243.71.222"


def test_dnsbl_provider_from_raw_normalizes_name() -> None:
    provider = DnsblProvider.from_raw("ZEN.SPAMHAUS.ORG")

    assert provider.name == "zen.spamhaus.org"


def test_dnsbl_provider_rejects_invalid_name() -> None:
    with pytest.raises(ConfigurationError, match="Invalid DNSBL provider name"):
        DnsblProvider.from_raw("not a provider")
