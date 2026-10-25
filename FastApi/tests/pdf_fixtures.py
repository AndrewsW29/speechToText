"""Builders for small, valid and deliberately hostile PDFs. Nothing here executes active content."""

from __future__ import annotations

import io

import pikepdf
from pikepdf import Array, Dictionary, Name, Pdf, String

EICAR = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"


def build_pdf(
    pages: int = 1,
    *,
    javascript: bool = False,
    launch: bool = False,
    embedded_file: bool = False,
    password: str | None = None,
) -> bytes:
    pdf = Pdf.new()
    for _ in range(pages):
        pdf.add_blank_page(page_size=(200, 200))
    if javascript:
        pdf.Root.OpenAction = Dictionary(
            S=Name.JavaScript, JS=String("app.alert('never executed');")
        )
    if launch:
        pdf.pages[0].Annots = Array(
            [
                pdf.make_indirect(
                    Dictionary(
                        Type=Name.Annot,
                        Subtype=Name.Link,
                        Rect=[0, 0, 10, 10],
                        A=Dictionary(S=Name.Launch, F=String("calc.exe")),
                    )
                )
            ]
        )
    if embedded_file:
        spec = pikepdf.AttachedFileSpec(pdf, b"hello", mime_type="text/plain")
        pdf.attachments["note.txt"] = spec
    out = io.BytesIO()
    if password:
        pdf.save(out, encryption=pikepdf.Encryption(user=password, owner=password))
    else:
        pdf.save(out)
    return out.getvalue()


def zip_renamed_as_pdf() -> bytes:
    return b"PK\x03\x04" + b"\x00" * 64


def damaged_xref(pages: int = 3) -> bytes:
    data = build_pdf(pages)
    cut = data.rfind(b"startxref")
    return data[:cut] + b"startxref\n999999\n%%EOF\n"
