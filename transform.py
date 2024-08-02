import sys
from lxml import etree
import copy
import re
from typing import List, Callable, Tuple, Any

# Namespace pro xtools
XHTML_NS = "http://www.w3.org/1999/xhtml"
NAMESPACE = "http:/ki.ujep.cz/ns/xtools"
FUNC_NS = "http://ki.ujep.cz/ns/functions"
NSMAP = {'xt': NAMESPACE, 'ak': "http://ki.ujep.cz/ns/akreditace"}


def split_list_by_predicate(lst: List[Any], predicate: Callable[[Any], bool]) -> Tuple[List[Any], List[Any]]:
    """
    Splits a list into two lists based on a predicate function.

    Parameters:
    lst (List[Any]): The input list to be split.
    predicate (Callable[[Any], bool]): A function that takes an element of the list and returns a boolean.

    Returns:
    Tuple[List[Any], List[Any]]: A tuple containing two lists:
                                 - The first list with elements that satisfy the predicate.
                                 - The second list with elements that do not satisfy the predicate.
    """
    matching = [element for element in lst if predicate(element)]
    non_matching = [element for element in lst if not predicate(element)]
    return matching, non_matching


def aname(context, element):
    def titul_pred(titul):
        return titul not in ["PhD.", "CSc.", "DrSc.", "DiS.", "MBA", "LL.M", "dr. h. c."]

    assert len(element) == 1
    element = element[0]
    jmeno = element.xpath("string(ak:jméno)", namespaces=NSMAP)
    tituly = re.split(r"[\s,]+", element.xpath("string(ak:tituly)", namespaces=NSMAP))
    tituly = [t for t in tituly if t] # odstraníme případné prázdné
    tituly_pred, tituly_za = split_list_by_predicate(tituly, titul_pred)

    if tituly_pred:
        jmeno = " ".join(tituly_pred) + " " + jmeno

    if tituly_za:
        jmeno = jmeno + ", " + ", ".join(tituly_za)

    return jmeno

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
    # Načtení XSLT skriptu
    xslt_doc = etree.parse(xslt_filename)


    # Nastavení rozšíření (pokud jsou poskytována)
    if extensions:
        ns_ext = {("http://ki.ujep.cz/ns/functions", name): func for name, func in extensions.items()}
        transform = etree.XSLT(xslt_doc, extensions=ns_ext)
    else:
         transform = etree.XSLT(xslt_doc)

    # Provádí transformaci
    result = transform(xml_doc)

    return result


def xpath_reg_function(functions):
    ns = etree.FunctionNamespace(None)
    for name, function in functions.items():
        ns[name] = function

def replace_xt_string(root):
    xt_contents_elements = root.xpath('//xt:string', namespaces=NSMAP)
    for xt_elem in xt_contents_elements:
        id = xt_elem.get('idref', None)
        f = xt_elem.get('f', "string")
        if xt_elem.get('xpath') is None and id is not None:
            xt_elem.set("xpath", f"#{id}")

        xpath_expr = xt_elem.get('xpath')

        xpath_expr = re.sub(r"^\#(\w+)", r"//*[@id='\1']", xpath_expr)
        xpath_expr = f"{f}({xpath_expr})"
        print(xpath_expr, file=sys.stderr)
        result_text = xt_elem.xpath(xpath_expr, namespaces=NSMAP)

        if id is not None:
            anchor = etree.Element("{%s}a" % XHTML_NS)
            anchor.set("href", f"#{id}")
            anchor.text = str(result_text)
            xt_elem.append(anchor)
        else:
            xt_elem.text = str(result_text)

# Funkce pro nahrazení xt:contents elementů
def replace_xt_contents(root):
    # Vyhledání všech xt:contents elementů
    xt_contents_elements = root.xpath('//xt:contents', namespaces=NSMAP)

    for xt_elem in xt_contents_elements:
        # Získání xpath výrazu z atributu
        xpath_expr = xt_elem.get('xpath')
        xpath_expr = re.sub(r"^\#(\w+)", r"//*[@id='\1']", xpath_expr)
        print(xpath_expr, file=sys.stderr)

        if xpath_expr:
            # Vyhodnocení xpath výrazu pro získání cílového obsahu
            result_nodes = xt_elem.xpath(xpath_expr, namespaces=NSMAP)

            if result_nodes:
                # Předpokládáme, že xpath výrazy vrací uzly, které mají být vloženy
                replacement_node = result_nodes[0]

                # Vložení hluboké kopie všech podřízených uzlů replacement_node do xt_elem
                for child in replacement_node:
                    xt_elem.append(copy.deepcopy(child))

                if replacement_node.text:
                    xt_elem.text = replacement_node.text


def main(xml_file):
    # Načtení XML dokumentu ze souboru
    with open(xml_file, 'rb') as file:
        root = etree.parse(file)

    xpath_reg_function(dict(aname=aname))

    replace_xt_string(root)
    replace_xt_contents(root)

    trans_root = transform_with_xslt(root, "transform.xslt")

    # Výstup výsledného dokumentu
    print(etree.tostring(trans_root, pretty_print=True, encoding="UTF-8").decode())

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <xml_file>")
        sys.exit(1)

    xml_file = sys.argv[1]
    main(xml_file)
