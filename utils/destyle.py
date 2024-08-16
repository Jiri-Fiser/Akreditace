from bs4 import BeautifulSoup

# Otevřete HTML soubor
with open("test_akreditace.html", "r", encoding="utf-8") as file:
    soup = BeautifulSoup(file, "html.parser")

# Odstraňte všechny tagy <style> a atributy stylů
for style in soup.find_all("style"):
    style.decompose()

for tag in soup.find_all(True):
    if "style" in tag.attrs:
        del tag.attrs["style"]

# Uložte upravený soubor
with open("output.html", "w", encoding="utf-8") as file:
    file.write(str(soup.prettify()))
