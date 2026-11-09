import argparse
import posixpath
import re
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from shutil import copyfile, copytree, ignore_patterns
from urllib.parse import quote, unquote, urljoin, urlsplit


PUBLIC_FILES = (
    "index.html",
    "autor.html",
    "logo.html",
    "style.css",
    "logo.css",
    "filmes/filme.css",
    "filmes/filme1.html",
    "filmes/filme2.html",
)


class ReferenceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references: list[tuple[str, str]] = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in {"href", "src"}:
                self.references.append((name, value or ""))


@dataclass
class Card:
    heading: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    status: list[str] = field(default_factory=list)


class CatalogParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cards: dict[str, list[Card]] = {}
        self.card: Card | None = None
        self.div_depth = 0
        self.text: list[str] | None = None
        self.text_tag = ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = (attrs.get("class") or "").split()
        if tag == "div":
            if self.card is None and "filme" in classes:
                self.card = Card()
                self.cards.setdefault(attrs.get("id") or "", []).append(self.card)
            if self.card is not None:
                self.div_depth += 1

        if self.card is None:
            return
        if tag == "a" and "href" in attrs:
            self.card.links.append(attrs["href"] or "")
        elif tag == "h2":
            self.text, self.text_tag = self.card.heading, tag
        elif tag == "span" and "status-filme" in classes:
            self.text, self.text_tag = self.card.status, tag
        elif tag == "br" and self.text is not None:
            self.text.append(" ")

    def handle_endtag(self, tag):
        if tag == self.text_tag:
            self.text, self.text_tag = None, ""
        if tag == "div" and self.card is not None:
            self.div_depth -= 1
            if self.div_depth == 0:
                self.card = None
                self.text, self.text_tag = None, ""

    def handle_data(self, data):
        if self.text is not None:
            self.text.append(data)


class TitleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.parts.append(data)


def prepare_site(source: Path, destination: Path) -> None:
    images = source / "img"
    if destination.resolve().is_relative_to(images.resolve()):
        raise ValueError("A pasta de publicação deve ficar fora da pasta img.")

    destination.mkdir(parents=True)
    for filename in PUBLIC_FILES:
        target = destination / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        copyfile(source / filename, target)
    copytree(images, destination / "img", ignore=ignore_patterns(".*"))


def published_paths(site: Path) -> set[str]:
    return {file.relative_to(site).as_posix() for file in site.rglob("*") if file.is_file()}


def resolve_local_path(page_url: str, reference: str) -> str | None:
    url = reference.strip().replace("\\", "/")
    parts = urlsplit(url)
    if parts.scheme or parts.netloc:
        return None
    path = unquote(urlsplit(urljoin(page_url, url)).path)
    resolved = posixpath.normpath(path)
    if path.endswith("/"):
        return resolved.rstrip("/") + "/index.html"
    return resolved


def validate_links(site: Path, base_path: str) -> list[str]:
    files = published_paths(site)
    errors = []
    if "index.html" not in files:
        errors.append("index.html: arquivo inicial ausente na raiz da publicação.")

    for filename in sorted(files):
        if not filename.lower().endswith((".html", ".htm")):
            continue

        page_url = "https://site.invalid" + base_path + quote(filename)
        parser = ReferenceParser()
        parser.feed((site / filename).read_text(encoding="utf-8"))
        parser.close()

        for attribute, reference in parser.references:
            label = f"{filename}: {attribute}={reference!r}"
            try:
                resolved = resolve_local_path(page_url, reference)
            except ValueError:
                errors.append(f"{label} é uma URL inválida.")
                continue

            if resolved is None:
                continue
            if not resolved.startswith(base_path):
                errors.append(f"{label} resolve para {resolved!r}, fora de {base_path}.")
                continue

            target = resolved.removeprefix(base_path)
            if target not in files:
                errors.append(f"{label} resolve para {target!r}, que não existe na publicação.")

    return errors


def normalize_title(parts: list[str]) -> str:
    title = " ".join("".join(parts).split())
    title = title.removesuffix("Mais vistos").rstrip()
    return re.sub(r"\s*\(\d{4}\)$", "", title)


def validate_catalog(site: Path, base_path: str) -> list[str]:
    parser = CatalogParser()
    parser.feed((site / "index.html").read_text(encoding="utf-8"))
    parser.close()

    page_url = "https://site.invalid" + base_path + "index.html"
    errors = []
    for number in range(1, 11):
        card_id = f"filme{number}"
        label = f"index.html: card {card_id}"
        cards = parser.cards.get(card_id, [])
        if len(cards) != 1:
            errors.append(f"{label} deve aparecer uma vez.")
            continue

        card = cards[0]
        if number > 2:
            if card.links or " ".join("".join(card.status).split()) != "Em breve":
                errors.append(f"{label} deve exibir 'Em breve' sem link.")
            continue

        expected_path = f"filmes/{card_id}.html"
        if len(card.links) != 1:
            errors.append(f"{label} deve ter um link para {expected_path!r}.")
            continue

        reference = card.links[0]
        resolved = resolve_local_path(page_url, reference)
        expected_title = normalize_title(card.heading)
        actual_title = ""
        if resolved and resolved.startswith(base_path) and resolved.endswith((".html", ".htm")):
            title = TitleParser()
            title.feed((site / resolved.removeprefix(base_path)).read_text(encoding="utf-8"))
            title.close()
            actual_title = normalize_title(title.parts)
        if resolved != base_path + expected_path or not expected_title or actual_title != expected_title:
            errors.append(
                f"{label}: esperado {expected_title or '(sem nome)'!r} em {expected_path!r}, "
                f"encontrado {actual_title or '(sem título)'!r} em {reference!r}."
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida os arquivos publicados no GitHub Pages.")
    parser.add_argument("--source", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, help="Pasta nova para preparar a publicação.")
    parser.add_argument("--base-path", default="/germinaFlix/")
    args = parser.parse_args()

    site = args.source
    try:
        if args.output is not None:
            prepare_site(args.source, args.output)
            site = args.output
            print("Arquivos preparados para publicação:", flush=True)
            print("\n".join(sorted(published_paths(site))), flush=True)
        errors = validate_links(site, args.base_path)
        if not errors:
            errors = validate_catalog(site, args.base_path)
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1

    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1

    print("Home, referências locais e cards validados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
