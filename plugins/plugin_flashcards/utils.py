#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from html.parser import HTMLParser

# --- Utilitário para remoção de tags HTML ---
class HTMLTextStripper(HTMLParser):
    """Classe para remover tags HTML do texto."""
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_html_tags(html):
    """Remove tags HTML do texto, inclusive o conteúdo de <style>."""
    html = re.sub(r'<style.*?>.*?</style>', '', html, flags=re.DOTALL)
    stripper = HTMLTextStripper()
    stripper.feed(html)
    return stripper.get_data()
