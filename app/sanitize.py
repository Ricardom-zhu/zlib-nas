"""Render untrusted descriptions using a deliberately small HTML vocabulary."""
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlsplit


class DescriptionParser(HTMLParser):
    allowed = {"p", "br", "b", "i", "em", "strong", "u", "a"}
    blocked = {"script", "style", "iframe", "object", "svg", "math", "template"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.output = []
        self.stack = []
        self.hidden = []

    def handle_starttag(self, tag, attrs):
        if self.hidden:
            if tag in self.blocked:
                self.hidden.append(tag)
            return
        if tag in self.blocked:
            self.hidden.append(tag)
            return
        if tag not in self.allowed:
            return
        attr = ""
        if tag == "a":
            href = dict(attrs).get("href") or ""
            try:
                valid = urlsplit(href).scheme.lower() in {"http", "https"}
            except ValueError:
                valid = False
            if valid and not any(ord(ch) < 32 for ch in href):
                attr = f' href="{escape(href, quote=True)}" rel="noreferrer noopener"'
        self.output.append(f"<{tag}{attr}>")
        if tag != "br":
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag != "br":
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if self.hidden:
            if tag == self.hidden[-1]:
                self.hidden.pop()
            return
        if tag in self.stack:
            while self.stack:
                current = self.stack.pop()
                self.output.append(f"</{current}>")
                if current == tag:
                    break

    def handle_data(self, data):
        if not self.hidden:
            self.output.append(escape(data))


def clean_description(value: str) -> str:
    parser = DescriptionParser()
    parser.feed(str(value or "")[:200000])
    parser.close()
    return "".join(parser.output) + "".join(f"</{tag}>" for tag in reversed(parser.stack))
