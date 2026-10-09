import pytest

from triage import triage


def test_ac1_60_affected_users_p1_sla2():
    assert triage({"title": "Issue", "affected_users": 60}) == {
        "priority": "P1",
        "queue": "General",
        "sla_hours": 2,
    }


def test_ac2_email_outage_p1():
    assert triage({"title": "Email outage"})["priority"] == "P1"


def test_ac3_slow_download_speed_p4_whole_word_rule():
    assert triage({"title": "Slow download speed"})["priority"] == "P4"


def test_ac4_12_users_p2_sla8():
    assert triage({"title": "Issue", "affected_users": 12}) == {
        "priority": "P2",
        "queue": "General",
        "sla_hours": 8,
    }


def test_ac5_urgent_cannot_print_p2():
    assert triage({"title": "URGENT: cannot print"})["priority"] == "P2"


def test_ac6_3_users_p3_sla24():
    assert triage({"title": "Issue", "affected_users": 3}) == {
        "priority": "P3",
        "queue": "General",
        "sla_hours": 24,
    }


def test_ac7_laptop_wifi_broken_queue_network_order_matters():
    assert triage({"title": "Laptop wifi broken"})["queue"] == "Network"


def test_ac10_vip_raises_priority_one_level_after_r2():
    assert triage({"title": "Issue", "affected_users": 3, "customer_tier": "vip"})["priority"] == "P2"


def test_ac11_security_queue_is_checked_first():
    assert triage({"title": "Phishing wifi breach"})["queue"] == "Security"


def test_ac12_invalid_customer_tier_raises_value_error():
    with pytest.raises(ValueError):
        triage({"title": "Issue", "customer_tier": "gold"})


def test_ac8_password_reset_queue_access():
    assert triage({"title": "Password reset"})["queue"] == "Access"


def test_ac9_empty_title_and_zero_users_raise_value_error():
    with pytest.raises(ValueError):
        triage({"title": "", "affected_users": 1})
    with pytest.raises(ValueError):
        triage({"title": "Issue", "affected_users": 0})
