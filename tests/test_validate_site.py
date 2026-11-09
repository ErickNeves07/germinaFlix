import subprocess
import sys
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

    def write_catalog(self, mufasa_destination="filmes/filme2.html", pending_link=""):
        self.write(
            self.site,
            "filmes/filme1.html",
            "<title>Homem-Aranha: Através do Aranhaverso</title>",
        )
        self.write(self.site, "filmes/filme2.html", "<title>Mufasa: O Rei Leão (2024)</title>")
        active = (
            '<div class="filme" id="filme1"><a href="filmes/filme1.html">'
            "<h2>Homem-Aranha: Através do Aranhaverso (2023)</h2></a></div>"
            f'<div class="filme" id="filme2"><a href="{mufasa_destination}">'
            "<h2>Mufasa:  O Rei Leão (2024) <span>Mais vistos</span></h2></a></div>"
        )
        pending = "".join(
            f'<div class="filme" id="filme{number}"><div class="card">'
            f'<span class="status-filme">Em breve</span>{pending_link if number == 3 else ""}'
            "</div></div>"
            for number in range(3, 11)
        )
        self.write(self.site, "index.html", active + pending)

    def run_site_validator(self):
        script = Path(__file__).resolve().parents[1] / "scripts" / "validate_site.py"
        return subprocess.run(
            [sys.executable, "-X", "utf8", str(script), "--source", str(self.site)],
            capture_output=True,
            encoding="utf-8",
            check=False,
        )

    def test_rejects_existing_destination_for_wrong_film(self):
        self.write_catalog(mufasa_destination="filmes/filme1.html")

        result = self.run_site_validator()

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("index.html", result.stderr)
        self.assertIn("filmes/filme1.html", result.stderr)
        self.assertIn("Mufasa: O Rei Leão", result.stderr)
        self.assertIn("Homem-Aranha: Através do Aranhaverso", result.stderr)

    def test_accepts_titles_with_year_badge_and_extra_spaces(self):
        self.write_catalog()

        result = self.run_site_validator()

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_incorrect_title_at_expected_destination(self):
        self.write_catalog()
        self.write(self.site, "filmes/filme2.html", "<title>Outro filme</title>")

        result = self.run_site_validator()

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("Mufasa: O Rei Leão", result.stderr)
        self.assertIn("Outro filme", result.stderr)

    def test_rejects_pending_card_with_link(self):
        self.write_catalog(pending_link='<a href="filmes/filme1.html">Filme</a>')

        result = self.run_site_validator()

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("filme3", result.stderr)
        self.assertIn("Em breve", result.stderr)

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
