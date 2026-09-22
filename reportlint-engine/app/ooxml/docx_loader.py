"""Low-level access to a .docx's constituent XML parts. Pure access only —
no interpretation happens here (see style_resolver.py / structure_extractor.py)."""

import zipfile
from lxml import etree

MAX_MEMBER_SIZE = 200 * 1024 * 1024  # 200MB guard against zip bombs
MAX_MEMBER_COUNT = 5000


class InvalidDocxError(Exception):
    pass


class DocxPackage:
    def __init__(self):
        self.document_tree: etree._ElementTree | None = None
        self.styles_tree: etree._ElementTree | None = None
        self.numbering_tree: etree._ElementTree | None = None
        self.settings_tree: etree._ElementTree | None = None
        self.media: dict[str, bytes] = {}
        self.rels: dict[str, str] = {}

    @classmethod
    def load(cls, path: str) -> "DocxPackage":
        if not zipfile.is_zipfile(path):
            raise InvalidDocxError(f"{path} is not a valid ZIP/.docx file")

        pkg = cls()
        try:
            with zipfile.ZipFile(path) as zf:
                infos = zf.infolist()
                if len(infos) > MAX_MEMBER_COUNT:
                    raise InvalidDocxError("Too many entries in archive (possible zip bomb)")
                for info in infos:
                    if info.file_size > MAX_MEMBER_SIZE:
                        raise InvalidDocxError(f"Entry {info.filename} exceeds size guard")

                names = set(zf.namelist())
                if "word/document.xml" not in names:
                    raise InvalidDocxError("word/document.xml missing — not a valid .docx")

                pkg.document_tree = etree.fromstring(zf.read("word/document.xml")).getroottree()

                if "word/styles.xml" in names:
                    pkg.styles_tree = etree.fromstring(zf.read("word/styles.xml")).getroottree()
                if "word/numbering.xml" in names:
                    pkg.numbering_tree = etree.fromstring(zf.read("word/numbering.xml")).getroottree()
                if "word/settings.xml" in names:
                    pkg.settings_tree = etree.fromstring(zf.read("word/settings.xml")).getroottree()

                for name in names:
                    if name.startswith("word/media/"):
                        pkg.media[name] = zf.read(name)

                rels_path = "word/_rels/document.xml.rels"
                if rels_path in names:
                    rels_root = etree.fromstring(zf.read(rels_path))
                    rel_ns = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}
                    for rel in rels_root.findall("r:Relationship", rel_ns):
                        pkg.rels[rel.get("Id")] = rel.get("Target")
        except zipfile.BadZipFile as e:
            raise InvalidDocxError(f"Corrupted zip: {e}") from e
        except etree.XMLSyntaxError as e:
            raise InvalidDocxError(f"Malformed XML inside docx: {e}") from e

        return pkg
