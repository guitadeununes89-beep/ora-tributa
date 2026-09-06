from lxml import etree
from tributaria_importers import secure_xml_parser


def test_external_entity_is_not_expanded() -> None:
    payload = b'<!DOCTYPE x [<!ENTITY external SYSTEM "file:///not-allowed">]><x>&external;</x>'
    root = etree.fromstring(payload, parser=secure_xml_parser())

    assert root.text is None
