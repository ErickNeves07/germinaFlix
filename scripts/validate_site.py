import argparse
import posixpath
import sys
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
                url = reference.strip().replace("\\", "/")
                parts = urlsplit(url)
                if parts.scheme or parts.netloc:
                    continue
                path = unquote(urlsplit(urljoin(page_url, url)).path)
            except ValueError:
                errors.append(f"{label} é uma URL inválida.")
                continue

            resolved = posixpath.normpath(path)
            if path.endswith("/"):
                resolved = resolved.rstrip("/") + "/index.html"
            if not resolved.startswith(base_path):
                errors.append(f"{label} resolve para {resolved!r}, fora de {base_path}.")
                continue

            target = resolved.removeprefix(base_path)
            if target not in files:
                errors.append(f"{label} resolve para {target!r}, que não existe na publicação.")

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
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1

    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1

    print("Home e referências locais validadas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
