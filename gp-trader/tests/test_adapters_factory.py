def test_factory_returns_local(tmp_path):
    from gptrader.adapters.factory import make_bus, make_executor, make_index
    from gptrader.config import settings

    # redirect writes to tmp so we don't touch repo data/
    settings.data_dir = tmp_path

    bus = make_bus()
    idx = make_index()
    ex = make_executor()

    assert bus.__class__.__name__ == "LocalEventBus"
    assert idx.__class__.__name__ == "LocalIndex"
    assert ex.__class__.__name__ in {"NoopExecutor", "StubExecutor"}

    # publish a minimal news event via the bus
    ev = {
        "v": 1,
        "topic": "news.v1",
        "symbol": "AAPL",
        "ts": "2025-01-01T00:00:00Z",
        "headline": "Test",
        "url": None,
        "sentiment_hint": None,
        "partition_key": "AAPL",
    }
    bus.publish("news.v1", [ev])

    # exercise the index: upsert & search
    idx.upsert([{"id": "1", "text": "Apple guidance strong", "symbol": "AAPL"}])
    res = idx.search("Apple", k=1)
    assert isinstance(res, list)
