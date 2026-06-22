from bs4 import BeautifulSoup


def clean_html(html_content):

    if not html_content:
        return ""

    soup = BeautifulSoup(html_content, "html.parser")

    text = soup.get_text(separator="\n")

    return text.strip()