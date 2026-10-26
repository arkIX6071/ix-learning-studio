"""Manual-release build guards. No network, no source mutations."""
import hashlib
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import ixls_release as rel


class ReleaseGuard(unittest.TestCase):
    def test_manifest_and_immutable_glossary(self):
        self.assertGreaterEqual(rel.verify_manifest(ROOT), 30)
        self.assertEqual(rel.sha256(ROOT / 'lessons/rs-l04/glossary.th.json'), rel.OWNER_APPROVED_GLOSSARY_SHA256)

    def test_workflow_manual_only(self):
        w = (ROOT / '.github/workflows/ixls-pages-manual.yml').read_text()
        self.assertRegex(w, r'(?m)^on:\s*\n\s+workflow_dispatch:')
        self.assertNotRegex(w, r'(?m)^\s+(push|schedule|pull_request):')
        self.assertIn("github.ref == 'refs/heads/main'", w)
        self.assertIn('OWNER_CONFIRM', w)
        self.assertIn('github.sha', w)
        self.assertIn('actions/deploy-pages@v4', w)
        self.assertIn('name: github-pages', w)

    def test_allowlist_and_broken_links(self):
        with tempfile.TemporaryDirectory(prefix='ixls-staged-') as tmp:
            stage = Path(tmp) / 'site'
            rel.build(ROOT, stage)
            have = {p.relative_to(stage).as_posix() for p in stage.rglob('*') if p.is_file()}
            self.assertEqual(have, rel.STAGED)
            for forbidden in ('tests/results.json', 'docs/RELEASE_006D_OWNER_DECISIONS.md',
                              'lessons/rs-l04/lesson.yaml', 'SHA256SUMS.txt'):
                self.assertNotIn(forbidden, have)
            self.assertTrue((stage / 'CODE_AND_CONTENT_RIGHTS.md').exists())
            self.assertGreaterEqual(rel.check_links(stage), 20)

    def test_tampered_approved_glossary_rejected(self):
        with tempfile.TemporaryDirectory(prefix='ixls-tamper-') as tmp:
            copy = Path(tmp) / 'source'
            shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns('*.pyc', '__pycache__'))
            glossary = copy / 'lessons/rs-l04/glossary.th.json'
            glossary.write_bytes(glossary.read_bytes() + b' ')
            with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
                rel.verify_manifest(copy)

    def test_legacy_hashes_and_exact_links(self):
        for relative, expected in rel.UNCHANGED_LESSONS.items():
            self.assertEqual(rel.sha256(ROOT / relative), expected)
        html = (ROOT / 'lessons/rs-l04/index.html').read_text()
        self.assertIn('href="../../CODE_AND_CONTENT_RIGHTS.md"', html)
        self.assertIn('href="../../"', html)
        self.assertEqual(len(re.findall('class="lesson"', (ROOT/'index.html').read_text())), 3)


if __name__ == '__main__':
    unittest.main()
