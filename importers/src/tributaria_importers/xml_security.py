from lxml import etree


def secure_xml_parser() -> etree.XMLParser:
    """Create an XML parser with external resources and entity resolution disabled."""
    return etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        load_dtd=False,
        recover=False,
        huge_tree=False,
    )
