"""Tests de la lógica de siembra geo (plan.md §F2.4)."""

from __future__ import annotations

from etl.common.capas_geo import _url_firmada


class _Resp:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


def test_url_firmada_extrae_url_del_resultado(monkeypatch):
    monkeypatch.setattr(
        "etl.common.capas_geo.requests.get",
        lambda url, params=None, timeout=60: _Resp(
            {"result": {"url": "https://s3.amazonaws.com/limites-colombia.zip"}}
        ),
    )
    url = _url_firmada()
    assert url.startswith("https://s3")


def test_descargar_con_limite_devuelve_bytes(monkeypatch):
    from etl.common.descargas import descargar_con_limite

    class _RespBytes:
        headers = {"Content-Length": "10"}

        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size=1024):
            yield b"01234"
            yield b"56789"

        def close(self):
            pass

    monkeypatch.setattr(
        "etl.common.descargas.requests.get",
        lambda url, stream=False, timeout=600, **kw: _RespBytes(),
    )
    contenido = descargar_con_limite("http://test", max_bytes=100)
    assert len(contenido) == 10
