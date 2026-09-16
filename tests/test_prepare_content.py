import base64
import importlib.util
import tempfile
import unittest
from pathlib import Path


SPEC = importlib.util.spec_from_file_location("prepare_content", Path("scripts/prepare-content.py"))
prepare_content = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(prepare_content)


class PrepareContentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.assets = self.root / "build assets"
        self.renderer = self.root / "renderer.py"
        self.renderer.write_text(
            "#!/usr/bin/env python3\n"
            "import pathlib,sys\n"
            "out=pathlib.Path(sys.argv[sys.argv.index('-o')+1])\n"
            "out.write_bytes(b'%PDF-1.4\\n%%EOF')\n",
            encoding="utf-8",
        )
        self.renderer.chmod(0o755)
        self.preparer = prepare_content.Preparer(self.assets, [str(self.renderer)], False)

    def tearDown(self):
        self.temp.cleanup()

    def test_nested_image_mermaids_order_and_safe_attributes(self):
        chapter = self.root / "chapters" / "nested"
        image_dir = chapter / "pictures"
        image_dir.mkdir(parents=True)
        (image_dir / "an image.png").write_bytes(base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        ))
        source = chapter / "chapter.md"
        source.write_text(
            '![A & B](<pictures/an image.png>){#fig:ok width=50% align=left}\n'
            '```mermaid {#fig:one caption="One & only"}\ngraph TD; A-->B\n```\n'
            'middle\n'
            '```mermaid {#fig:two caption="Second" align=right}\ngraph TD; B-->C\n```\n',
            encoding="utf-8",
        )
        result = self.preparer.prepare(source)
        self.assertIn(r"width=0.5\linewidth,height=0.85\textheight,keepaspectratio", result)
        self.assertIn(r"\raggedright", result)
        self.assertIn(r"\caption{A \& B}", result)
        self.assertEqual(len(list(self.assets.glob("*.png"))), 1)
        self.assertEqual(len(list(self.assets.glob("*.pdf"))), 2)
        self.assertLess(result.index("fig:one"), result.index("middle"))
        self.assertLess(result.index("middle"), result.index("fig:two"))

    def test_missing_image_is_visible_and_does_not_inject_tex(self):
        source = self.root / "chapter.md"
        source.write_text(r"![bad # $](missing file.png){#bad}{ignored}", encoding="utf-8")
        result = self.preparer.prepare(source)
        self.assertIn("Missing image:", result)
        self.assertIn(r"bad \# \$", result)
        self.assertNotIn(r"\includegraphics", result)

    def test_invalid_dimensions_fall_back(self):
        self.assertEqual(prepare_content.dimension("evil", r"\linewidth"), r"\linewidth")
        self.assertEqual(prepare_content.dimension("1cm", "fallback"), "1cm")
        self.assertEqual(prepare_content.dimension("125%", "fallback"), r"1\linewidth")


if __name__ == "__main__":
    unittest.main()
