from app.ratelimit import RateLimiter, client_key


def test_allows_up_to_limit():
    rl = RateLimiter(max_requests=3, window_seconds=60.0)
    assert rl.check("ip1", now=0.0) is True
    assert rl.check("ip1", now=1.0) is True
    assert rl.check("ip1", now=2.0) is True


def test_blocks_over_limit():
    rl = RateLimiter(max_requests=3, window_seconds=60.0)
    rl.check("ip1", now=0.0)
    rl.check("ip1", now=1.0)
    rl.check("ip1", now=2.0)
    assert rl.check("ip1", now=3.0) is False


def test_window_slides():
    rl = RateLimiter(max_requests=2, window_seconds=10.0)
    assert rl.check("ip1", now=0.0) is True
    assert rl.check("ip1", now=1.0) is True
    assert rl.check("ip1", now=2.0) is False
    # after window passes, old hits expire
    assert rl.check("ip1", now=12.0) is True


def test_keys_independent():
    rl = RateLimiter(max_requests=1, window_seconds=60.0)
    assert rl.check("ip1", now=0.0) is True
    assert rl.check("ip2", now=0.0) is True
    assert rl.check("ip1", now=1.0) is False


def test_client_key_prefers_forwarded_for():
    assert client_key(x_forwarded_for="1.2.3.4, 5.6.7.8", client_host="10.0.0.1") == "1.2.3.4"


def test_client_key_falls_back_to_host():
    assert client_key(x_forwarded_for=None, client_host="10.0.0.1") == "10.0.0.1"
    assert client_key(x_forwarded_for="", client_host="10.0.0.1") == "10.0.0.1"


def test_client_key_unknown_when_nothing():
    assert client_key(x_forwarded_for=None, client_host=None) == "unknown"
