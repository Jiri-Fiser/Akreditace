import re
from typing import List, Callable, Any, Tuple

NSMAP = {'ak': "http://ki.ujep.cz/ns/akreditace"}

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
    tituly = (re.split(r"[\s,]+", element.xpath("string(ak:tituly)", namespaces=NSMAP)))
    tituly = [t for t in tituly if t] # odstraníme případné prázdné
    tituly_pred, tituly_za = split_list_by_predicate(tituly, titul_pred)

    if tituly_pred:
        jmeno = " ".join(tituly_pred) + " " + jmeno

    if tituly_za:
        jmeno = jmeno + ", " + ", ".join(tituly_za)

    return jmeno