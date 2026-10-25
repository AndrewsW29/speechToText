"""Detect (never execute) and optionally strip active content: scripts, launches, attachments."""

from __future__ import annotations

import io
from collections.abc import Iterator

import pikepdf
from pikepdf import Name


def _walk(obj: object, seen: set[tuple[int, int]]) -> Iterator[pikepdf.Dictionary]:
    """Every dictionary reachable from `obj`, direct ones included, each visited once."""
    if not isinstance(obj, pikepdf.Object):
        return
    gen = obj.objgen
    if gen != (0, 0):
        if gen in seen:
            return
        seen.add(gen)
    if isinstance(obj, pikepdf.Dictionary):
        yield obj
        for key in list(obj.keys()):
            yield from _walk(obj.get(key), seen)
    elif isinstance(obj, pikepdf.Array):
        for item in obj:
            yield from _walk(item, seen)
    elif isinstance(obj, pikepdf.Stream):
        yield from _walk(obj.stream_dict, seen)


def _dictionaries(pdf: pikepdf.Pdf) -> Iterator[pikepdf.Dictionary]:
    seen: set[tuple[int, int]] = set()
    yield from _walk(pdf.Root, seen)
    yield from _walk(pdf.trailer, seen)


def _action_kind(d: pikepdf.Dictionary) -> str | None:
    s = d.get("/S")
    if s == Name.JavaScript:
        return "javascript"
    if s == Name.Launch:
        return "launch"
    return None


def _scan(pdf: pikepdf.Pdf) -> set[str]:
    found: set[str] = set()
    for d in _dictionaries(pdf):
        if (kind := _action_kind(d)) is not None:
            found.add(kind)
        if "/JS" in d:
            found.add("javascript")
        if "/EF" in d or d.get("/Type") == Name.EmbeddedFile:
            found.add("embedded_file")
    names = pdf.Root.get("/Names")
    if isinstance(names, pikepdf.Dictionary):
        if "/JavaScript" in names:
            found.add("javascript")
        if "/EmbeddedFiles" in names:
            found.add("embedded_file")
    return found


def detect_active_content(data: bytes) -> set[str]:
    """Subset of {"javascript", "launch", "embedded_file"}; unreadable files report nothing."""
    try:
        with pikepdf.open(io.BytesIO(data)) as pdf:
            return _scan(pdf)
    except (pikepdf.PdfError, pikepdf.PasswordError):
        return set()


def strip_active_content(data: bytes) -> bytes:
    with pikepdf.open(io.BytesIO(data)) as pdf:
        root = pdf.Root
        for key in ("/OpenAction", "/AA"):
            if key in root:
                del root[key]
        names = root.get("/Names")
        if isinstance(names, pikepdf.Dictionary):
            for key in ("/JavaScript", "/EmbeddedFiles"):
                if key in names:
                    del names[key]
        for d in list(_dictionaries(pdf)):
            for key in ("/AA", "/JS", "/EF"):
                if key in d:
                    del d[key]
            if _action_kind(d) is not None:
                for key in list(d.keys()):
                    if key != "/Type":
                        del d[key]
        for page in pdf.pages:
            annots = page.get("/Annots")
            if annots is None:
                continue
            kept = [
                a
                for a in annots
                if "/A" not in a or _action_kind(a["/A"]) is None  # type: ignore[arg-type]
            ]
            page.Annots = pikepdf.Array(kept)
        out = io.BytesIO()
        pdf.save(out)
        return out.getvalue()
