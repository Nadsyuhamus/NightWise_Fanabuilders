"""Verify export integrity and source identity, not just metadata presence."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import provenance
from export_results import export_scenario


class ProvenanceTests(unittest.TestCase):
    def test_source_change_changes_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'models.py'
            source.write_text('original')
            with patch.object(provenance, 'ROOT', root):
                before = provenance.source_provenance()
                source.write_text('modified')
                after = provenance.source_provenance()
            self.assertNotEqual(before['source_manifest_sha256'], after['source_manifest_sha256'])

    def test_export_manifest_matches_actual_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            export_scenario('empty_night', directory)
            folder = Path(directory) / 'empty_night'
            metadata = json.loads((folder / 'run_metadata.json').read_text())
            self.assertEqual(metadata['actual_duration_s'], 120)
            self.assertEqual(set(metadata['output_sha256']), {p.name for p in folder.glob('*.csv')})
            for name, expected in metadata['output_sha256'].items():
                self.assertEqual(provenance.sha256(folder / name), expected)
            target = folder / 'impact_summary.csv'
            target.write_bytes(target.read_bytes() + b'altered')
            self.assertNotEqual(provenance.sha256(target), metadata['output_sha256'][target.name])


if __name__ == '__main__':
    unittest.main()
