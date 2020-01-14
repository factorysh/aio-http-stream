import time
from session import Session


def test_session():
    s = Session(10, 0.5)
    assert "beuha" not in s
    assert len(s) == 0
    s["beuha"] = 42
    assert "beuha" in s
    assert s["beuha"] == 42
    assert len(s) == 1
    assert s.garbage_collector() == 0
    assert "beuha" in s.keys()
    time.sleep(0.5)
    assert s.garbage_collector() == 1
    assert len(s) == 0
    assert "beuha" not in s
