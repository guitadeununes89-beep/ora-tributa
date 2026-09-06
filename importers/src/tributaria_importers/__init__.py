"""Safe ingestion adapters; no tax classification belongs in this package."""

from tributaria_importers.xml_security import secure_xml_parser

__all__ = ["secure_xml_parser"]
