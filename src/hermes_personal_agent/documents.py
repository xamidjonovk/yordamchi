"""Text extraction with page/part provenance. No macros or embedded code is executed."""
import csv
import io
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET


class TextHTML(HTMLParser):
    def __init__(self):
        super().__init__(); self.text = []; self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}: self.skip += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"}: self.skip = max(0, self.skip - 1)
        if tag in {"p", "div", "br", "li", "h1", "h2", "h3"}: self.text.append("\n")

    def handle_data(self, data):
        if not self.skip: self.text.append(data)


def extract(path):
    path = Path(path)
    extension = path.suffix.lower()
    if extension == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        if reader.is_encrypted: raise ValueError("Encrypted PDF: provide an unlocked copy")
        return [(f"page {i+1}", page.extract_text() or "") for i, page in enumerate(reader.pages)]
    if extension in {".docx", ".pptx", ".xlsx"}:
        with zipfile.ZipFile(path) as archive:
            if sum(item.file_size for item in archive.infolist()) > 200_000_000:
                raise ValueError("Expanded office document exceeds 200 MB")
            if extension == ".docx": names = ["word/document.xml"]
            elif extension == ".pptx": names = sorted(n for n in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n))
            else:
                # openpyxl reads cell values without running formulas or VBA.
                from openpyxl import load_workbook
                workbook = load_workbook(path, data_only=True, read_only=True)
                try:
                    return [(f"sheet {sheet.title}", "\n".join("\t".join(str(v) if v is not None else "" for v in row)
                        for row in sheet.iter_rows(values_only=True))) for sheet in workbook]
                finally: workbook.close()
            return [(name, "\n".join(t.text for t in ET.fromstring(archive.read(name)).iter()
                if t.tag.rsplit("}", 1)[-1] == "t" and t.text)) for name in names]
    if extension in {".html", ".htm"}:
        parser = TextHTML(); parser.feed(path.read_text(encoding="utf-8", errors="replace"))
        return [("document", " ".join(parser.text))]
    if extension in {".txt", ".md", ".csv", ".tsv", ".json", ".yaml", ".yml", ".xml", ".log", ".py", ".js", ".ts"}:
        raw = path.read_bytes()
        text = raw.decode("utf-16" if raw.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig", errors="replace")
        return [("document", text)]
    raise ValueError("Unsupported format; use Hermes document/vision tools, then import extracted text with its source citation")


def chunks(parts, size=1400, overlap=180):
    for location, text in parts:
        text = text.strip()
        start = 0
        while start < len(text):
            end = min(start + size, len(text))
            if end < len(text):
                boundary = text.rfind(" ", start + size // 2, end)
                if boundary > start: end = boundary
            yield location, start, text[start:end]
            if end == len(text): break
            start = max(start + 1, end - overlap)
