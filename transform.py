import sys
from lxml import etree
import re
from typing import List, Callable, Tuple, Any

from xfunction import aname
from xtools import Transformer, add_tag_to_class_and_replace

# Namespace pro xtools

NSMAP = {'ak': "http://ki.ujep.cz/ns/akreditace"}


def transform_with_xslt(xml_doc, xslt_filename, extensions=None):
    """
    Provádí XSLT transformaci na XML dokumentu pomocí XSLT skriptu.

    Args:
        xml_doc (etree._Element): Vstupní XML dokument jako etree objekt.
        xslt_filename (str): Cesta k XSLT souboru.
        extensions (dict): Nepovinný slovník mapující jména na funkce pro XPath výrazy.

    Returns:
        etree._Element: Výsledek transformace jako etree objekt.
    """
    xslt_doc = etree.parse(xslt_filename)
    if extensions:
        transform = etree.XSLT(xslt_doc, extensions=extensions)
    else:
         transform = etree.XSLT(xslt_doc)

    return transform(xml_doc)


def main(xml_file):
    # Načtení XML dokumentu ze souboru
    with open(xml_file, 'rb') as file:
        root = etree.parse(file)

    root.xinclude()

    transformer = Transformer(NSMAP, [aname])
    transformer.replace_all(root)
    trans_root = transform_with_xslt(root, "transform.xslt", extensions=transformer.extensions)

    for element in trans_root.xpath("//tag:*", namespaces = transformer.namespaces):
        add_tag_to_class_and_replace(element)

    namespaces = {'': 'http://www.w3.org/TR/html4/'}

    # Výstup výsledného dokumentu
    print(etree.tostring(trans_root, pretty_print=True, encoding="UTF-8").decode())


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <xml_file>")
        sys.exit(1)

    xml_file = sys.argv[1]
    main(xml_file)
