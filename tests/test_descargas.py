"""Pruebas del límite de tamaño de descargas (auditoría 2026-08-02, hallazgo 9)."""


import pytest

from etl.common.descargas import DescargaDemasiadoGrande, descargar_con_limite


def _resp_bytes(datos: bytes):
    class _Resp:
        headers = {"Content-Length": str(len(datos))}

        def __init__(self):
            self._resto = datos
            self.cerrado = False

        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size=1024 * 1024):
            while self._resto:
                trozo, self._resto = self._resto[:chunk_size], self._resto[chunk_size:]
                yield trozo

        def close(self):
            self.cerrado = True

    return _Resp()


def test_rechaza_por_content_length(monkeypatch):
    """Una fuente que declara más del tope se rechaza sin descargar."""

    class _Resp:
        headers = {"Content-Length": "999999999999"}
        cerrado = False

        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size=1024 * 1024):
            yield b""

        def close(self):
            self.cerrado = True

    monkeypatch.setattr("etl.common.descargas.requests.get", lambda *a, **k: _Resp())
    with pytest.raises(DescargaDemasiadoGrande):
        descargar_con_limite("https://x.example/a.zip", max_bytes=1024)


def test_rechaza_por_tamano_real(monkeypatch):
    """Sin Content-Length, corta el stream al superar el tope."""

    class _Resp:
        headers = {}

        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size=1024 * 1024):
            yield b"a" * 2048

        def close(self):
            pass

    monkeypatch.setattr("etl.common.descargas.requests.get", lambda *a, **k: _Resp())
    with pytest.raises(DescargaDemasiadoGrande):
        descargar_con_limite("https://x.example/a.zip", max_bytes=1024)


def test_descarga_completa(monkeypatch):
    resp = _resp_bytes(b"hola mundo")

    def fake_get(url, **kwargs):
        assert kwargs.get("stream") is True
        return resp

    monkeypatch.setattr("etl.common.descargas.requests.get", fake_get)
    assert descargar_con_limite("https://x.example/a.txt") == b"hola mundo"
    assert resp.cerrado
