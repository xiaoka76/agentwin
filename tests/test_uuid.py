"""UUID generation stability tests."""
from agentwin.core.auth import make_uuid


def test_uuid_stable():
    u1 = make_uuid("10.0.0.20", 5985, "Administrator", "winrm-password")
    u2 = make_uuid("10.0.0.20", 5985, "Administrator", "winrm-password")
    assert u1 == u2
    assert len(u1) == 12


def test_uuid_changes_with_password():
    u1 = make_uuid("10.0.0.20", 5985, "Administrator", "winrm-password")
    u2 = make_uuid("10.0.0.20", 22, "Administrator", "ssh-key")
    assert u1 != u2


def test_uuid_changes_with_port():
    u1 = make_uuid("10.0.0.20", 5985, "Administrator", "winrm-password")
    u2 = make_uuid("10.0.0.20", 5986, "Administrator", "winrm-password")
    assert u1 != u2
