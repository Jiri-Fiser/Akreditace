import copy
import sys
import textwrap
from typing import Callable
from lxml import etree
import re
import networkx as nx


def cycle(graph):
    graph = {key: [value] for key, value in graph.items()}
    G = nx.DiGraph(graph)
    try:
        cycle = nx.find_cycle(G, orientation='original')
        return cycle
    except nx.exception.NetworkXNoCycle:
        return []


class TransformerException(Exception):
    def __init__(self, message):
        super().__init__(f"{normalize_multiline_string(message)}")


def normalize_multiline_string(s: str) -> str:
    # Použití textwrap.dedent pro odstranění společného odsazení
    dedented_text = textwrap.dedent(s)

    # Rozdělení řetězce na jednotlivé řádky
    lines = dedented_text.splitlines()

    # Odstranění prvního prázdného řádku (pokud existuje)
    if lines and lines[0].strip() == '':
        lines = lines[1:]

    # Spojení řádků zpět do jednoho řetězce
    return '\n'.join(lines)


def estr(element: etree._Element, width: int = 80):
    def get_substring_after_last_slash(input_string):
        last_slash_index = input_string.rfind('/')

        if last_slash_index == -1:
            return input_string
        else:
            return input_string[last_slash_index + 1:]
    line = element.sourceline
    base = get_substring_after_last_slash(element.base)
    text = etree.tostring(element, encoding='unicode', method='xml', pretty_print=False)
    text = re.sub(r'xmlns(:[a-zA-Z_][\w\-.]*)?="[^"]*"', "", text)
    text = re.sub(r"\s+", " ", text)
    text = f"[{base}:{line:d}]" + text
    if len(text) > width:
        return text[:width] + "..."
    else:
        return text


def wrap_with_tag(elem, namespace):
    """
    Najde atribut elementu s daným jmenným prostorem, obalí element novým elementem se jménem a jmenným prostorem
    shodným s nalezeným atributem, a odstraní nalezený atribut.

    :param elem: lxml.etree.Element k obalení
    :param namespace: namespace, který se má hledat v atributech
    :return: obalený element
    """
    # Najdi atribut s daným jmenným prostorem
    attr_name = None
    for attr in elem.attrib:
        if etree.QName(attr).namespace == namespace:
            attr_name = attr
            break

    assert attr_name, "No attribute with the given namespace found."

    # Získej jméno a hodnotu atributu
    qname = etree.QName(attr_name)
    attr_value = elem.attrib.pop(attr_name)

    # Vytvoř nový obalující element
    wrapper = etree.Element(qname, nsmap={"tag": qname.namespace})

    # Přesuň původní element jako podřízený do nového elementu
    elem.getparent().replace(elem, wrapper)
    wrapper.set("value", attr_value)
    wrapper.append(elem)

    return wrapper


class Transformer:
    XHTML_NS = "http://www.w3.org/1999/xhtml"
    XT_NS = "http://ki.ujep.cz/ns/xtools"
    FUNC_NS = "http://ki.ujep.cz/ns/func"
    TAG_NS = "http://ki.ujep.cz/ns/xtags"

    def __init__(self, namespaces: list[str, str], functions: Callable):
        self.extensions = {(self.FUNC_NS, f.__name__): f for f in functions}
        self.namespaces = namespaces
        self.namespaces["xt"] = self.XT_NS
        self.namespaces["f"] = self.FUNC_NS
        self.namespaces["tag"] = self.TAG_NS

    def evaluate(self, node, xpath: str):
        e = etree.XPathEvaluator(node, namespaces=self.namespaces, extensions=self.extensions)
        print(xpath, file=sys.stderr)
        return e.evaluate(xpath)

    @staticmethod
    def xpath_substitution(xpath: str, function: str = None):
        xpath = re.sub(r"^#([\w_:-]+)", r"//*[@id='\1']", xpath)
        if function is not None:
            xpath = f"{function}({xpath})"
        return xpath

    def replace_xt_string(self, root):
        xt_contents_elements = self.evaluate(root, '//xt:string')
        for xt_elem in xt_contents_elements:
            idref = xt_elem.get('idref', None)
            if idref and "|" in idref:
                idref, function = idref.split("|")
                function = f"f:{function}"
            else:
                function = xt_elem.get('f', "string")
            if xt_elem.get('xpath') is None and idref is not None:
                xt_elem.set("xpath", f"#{idref}")

            xpath = xt_elem.get('xpath')
            if xpath is None:
                raise Transformer.no_xpath_exception_factory(xt_elem)

            xpath = self.xpath_substitution(xpath, function)
            result_text = str(self.evaluate(xt_elem, xpath))

            if idref is not None:
                anchor = etree.Element("{%s}a" % self.XHTML_NS)
                anchor.set("href", f"#{idref}")
                anchor.text = result_text
                xt_elem.append(anchor)
            else:
                xt_elem.text = str(result_text)

    def merge_elements(self, root):
        network = {}
        extended_elements = self.evaluate(root, "//*[@xt:extends]")
        for extended_element in extended_elements:
            xpath = self.xpath_substitution(extended_element.get('{%s}extends' % self.XT_NS))
            base_elements = self.evaluate(root, xpath)
            if len(base_elements) != 1:
                raise Transformer.node_exception_factory(extended_element, "1", base_elements)
            base_element = base_elements[0]
            network[extended_element] = base_element

        if loop := cycle(network):
            raise TransformerException("cycle in extends:\n" + "\n->\n".join(estr(e[0]) for e in loop) + "\n->...\n")

        while True:
            merges = [(base, extended) for extended, base in network.items() if base not in network]
            if not merges:
                break
            for _, extended in merges:
                del network[extended]
            for pair in merges:
                Transformer.extends(*pair)

    @staticmethod
    def extends(base, extended):
        base_nodes = {node.tag: node for node in base}
        extended_nodes = {node.tag: node for node in extended}

        if not(set(extended_nodes) <= set(base_nodes)):
            raise TransformerException(f"""
                {estr(extended)} 
                    is not subset of 
                {estr(base)} 
                difference: {set(extended_nodes) - set(base_nodes)}""")
        merged_nodes = []

        for tag in base_nodes.keys():
            if tag in extended_nodes:
                merged_nodes.append(extended_nodes[tag])
            else:
                merged_nodes.append(copy.deepcopy(base_nodes[tag]))

        for child in list(extended):
            extended.remove(child)
        extended.extend(merged_nodes)

    def replace_xt_contents(self, root):
        xt_contents_elements = self.evaluate(root, '//xt:contents')

        for xt_elem in xt_contents_elements:
            xpath = self.xpath_substitution(xt_elem.get('xpath'))
            if xpath is None:
                raise self.no_xpath_exception_factory(xt_elem)

            result_nodes = self.evaluate(xt_elem, xpath)
            if len(result_nodes) != 1:
                raise Transformer.node_exception_factory(xt_elem, "1", result_nodes)
            replacement_node = result_nodes[0]
            for child in replacement_node:
                xt_elem.append(copy.deepcopy(child))
                if replacement_node.text:
                    xt_elem.text = replacement_node.text

    def replace_xt_append(self, root):
        xt_contents_elements = self.evaluate(root, '//xt:append')

        for xt_elem in xt_contents_elements:
            xpath = self.xpath_substitution(xt_elem.get('xpath'))
            if xpath is None:
                Transformer.no_xpath_exception_factory(xt_elem)

            result_nodes = self.evaluate(xt_elem, xpath)
            assert len(result_nodes) >= 1
            for child in result_nodes:
                xt_elem.append(copy.deepcopy(child))

    def hoist_tags(self, root):
            tagged_elements = self.evaluate(root, "//*[@tag:*]")
            for tagged_element in tagged_elements:
                wrap_with_tag(tagged_element, Transformer.TAG_NS)

    def replace_all(self, root):
        self.merge_elements(root)
        self.replace_xt_string(root)
        self.replace_xt_contents(root)
        self.replace_xt_append(root)
        self.hoist_tags(root)

    @staticmethod
    def node_exception_factory(element, expected, result_nodes):
        lines = []
        lines.append("in element:")
        lines.append(estr(element))
        lines.append("xpath references invalid number of nodes")
        lines.append(f"expected number of nodes: {expected}")
        lines.append(f"actual number of nodes: {len(result_nodes)}")
        if result_nodes:
            lines.append("nodes:")
            for node in result_nodes:
                match node:
                    case etree._Element():
                        lines.append(estr(node))
                    case _:
                        lines.append(str(node))
        return TransformerException("\n".join(lines))

    @staticmethod
    def no_xpath_exception_factory(xt_elem):
        return TransformerException(f"""
                no xpath attribute in element:
                {estr(xt_elem)}""")

def add_tag_to_class_and_replace(element):
    """
    Přidá jméno elementu do atributu class (po mezeře) všech dětských elementů a nahradí předaný element jeho dětmi.

    :param element: lxml.etree.Element
    """
    localname = etree.QName(element).localname
    # Procházej všechny dětské elementy
    for child in element:
        if 'class' in child.attrib:
            child.attrib['class'] += ' tag_' + localname
        else:
            child.attrib['class'] = "tag_" + localname

    element[0].attrib['data-tag'] = element.get("value", "")

    # Získání rodiče předaného elementu
    parent = element.getparent()
    if parent is None:
        raise ValueError("The element has no parent. It might be the root element.")

    # Vložení dětí předaného elementu na místo předaného elementu
    for child in element:
        parent.insert(parent.index(element), child)

    # Odstranění předaného elementu
    parent.remove(element)


if __name__ == "__main__":
    with open("merge_test.xml", 'rb') as file:
        root = etree.parse(file)

    transformer = Transformer({}, [])
    transformer.replace_all(root)
    print(etree.tostring(root, pretty_print=True, encoding="UTF-8").decode())

