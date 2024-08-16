xmllint --xinclude zadost_2025/main.xml > input.xml && python3.11 transform.py input.xml  > output.html && prince  output.html
