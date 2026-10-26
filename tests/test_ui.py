from Dashboard import ui


def test_compact_scales_numbers():
    assert ui.compact(950) == "950"
    assert ui.compact(12_400) == "12.4K"
    assert ui.compact(6_517_873) == "6.5M"
    assert ui.compact(2_100_000_000) == "2.1B"


def test_times_avoids_misleading_zero():
    assert ui.times(0.01) == "<0.1x"
    assert ui.times(2.345) == "2.3x"
