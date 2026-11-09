import tempfile
import unittest
from pathlib import Path

from scripts.validate_site import prepare_site, validate_links


class SiteValidationTests(unittest.TestCase):
    def setUp(self):
        workspace = self.enterContext(tempfile.TemporaryDirectory())
        self.source = Path(workspace) / "source"
        self.site = Path(workspace) / "site"

    def write(self, root, path, content=""):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def test_prepares_only_published_files(self):
        paths = {
            "index.html",
            "autor.html",
            "logo.html",
            "style.css",
            "logo.css",
            "filmes/filme.css",
            "filmes/filme1.html",
            "filmes/filme2.html",
            "img/logo.png",
        }
        for path in paths | {"filmes/filme7.html", "filmes/aa.py"}:
            self.write(self.source, path)

        prepare_site(self.source, self.site)

        copied = {
            path.relative_to(self.site).as_posix()
            for path in self.site.rglob("*")
            if path.is_file()
        }
        self.assertEqual(copied, paths)

    def test_preparation_reports_a_missing_required_file(self):
        self.write(self.source, "index.html")
        self.write(self.source, "autor.html")

        with self.assertRaises(FileNotFoundError) as error:
            prepare_site(self.source, self.site)

        self.assertEqual(Path(error.exception.filename).name, "logo.html")

    def test_requires_the_home_at_the_package_root(self):
        self.write(self.site, "filmes/index.html")

        errors = validate_links(self.site, "/germinaFlix/")

        self.assertEqual(len(errors), 1)
        self.assertIn("index.html", errors[0])

    def test_resolves_local_urls_and_skips_external_urls(self):
        self.write(self.site, "index.html")
        self.write(self.site, "img/mulheranha (1).png")
        self.write(
            self.site,
            "filmes/filme1.html",
            """
            <img src="../img/mulheranha (1).png">
            <img src="/germinaFlix/img/mulheranha%20%281%29.png">
            <a href="../index.html?origem=filme#catalogo">Início</a>
            <a href="../">Início</a>
            <a href="#titulo">Título</a>
            <a href="">Filme</a>
            <a href="https://example.invalid/">Externo</a>
            <img src="//example.invalid/capa.png">
            <a href="mailto:teste@example.invalid">Contato</a>
            """,
        )

        self.assertEqual(validate_links(self.site, "/germinaFlix/"), [])

    def test_reports_source_and_path_for_invalid_references(self):
        self.write(self.source, "filmes/filme7.html")
        self.write(self.site, "index.html")
        self.write(self.site, "img/logo.png")
        self.write(
            self.site,
            "filmes/filme1.html",
            """
            <a href="filme7.html">Filme</a>
            <img src="../img/Logo.png">
            <img src="/img/logo.png">
            <img src="/germinaFlix/%2e%2e/img/logo.png">
            """,
        )

        errors = validate_links(self.site, "/germinaFlix/")

        self.assertEqual(len(errors), 4)
        for reference in (
            "filme7.html",
            "../img/Logo.png",
            "/img/logo.png",
            "/germinaFlix/%2e%2e/img/logo.png",
        ):
            with self.subTest(reference=reference):
                self.assertTrue(
                    any(
                        error.startswith("filmes/filme1.html:")
                        and repr(reference) in error
                        for error in errors
                    ),
                    errors,
                )
