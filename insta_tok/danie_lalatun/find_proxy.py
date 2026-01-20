
import re

html_content = """
<PASTE_HTML_CONTENT_HERE>
"""

# Regular expression to find elite proxies with HTTPS support
# This is a simplified regex and might need adjustments based on the actual HTML structure
proxy_regex = r"<tr><td>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</td><td>(\d+)</td><td>[A-Z]{2}</td><td class='hm'>.*?</td><td class='hm'>elite proxy</td><td class='hm'>yes</td><td class='hm'>.*?</td></tr>"

matches = re.findall(proxy_regex, html_content)

if matches:
    ip, port = matches[0]
    print(f"Found proxy: {ip}:{port}")
else:
    print("No suitable proxy found.")
