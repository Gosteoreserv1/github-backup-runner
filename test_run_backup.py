import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from run_backup import configuration, execute, REVISION


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.env = {'PRIMARY_TOKEN': 'fake', 'BACKUP_TOKEN': 'fake2',
                    'PRIMARY_METADATA_TOKEN': 'fake3'}

    def test_missing_secret_fails_closed(self):
        with self.assertRaises(ValueError):
            configuration({})

    def test_shell_injection_rejected(self):
        with self.assertRaises(ValueError):
            configuration(dict(self.env, TARGET_REPOSITORY='repo; echo bad'))

    def test_invalid_delivery_rejected(self):
        with self.assertRaises(ValueError):
            configuration(dict(self.env, DELIVERY_ID='bad/id'))

    def test_success_uses_pinned_private_code_and_saves_status(self):
        calls = []
        def fake(args, **kwargs):
            calls.append(args)
            if args[:2] == ['git', 'clone']:
                Path(args[-1]).mkdir()
            code = 1 if args[:4] == ['git', 'diff', '--cached', '--quiet'] else 0
            self.assertIsNotNone(kwargs['stdout'])
            return SimpleNamespace(returncode=code)
        self.assertEqual(execute(self.env, fake), 0)
        self.assertIn(['git', 'checkout', '--detach', REVISION], calls)
        self.assertIn(['python3', 'scripts/push_controller.py'], calls)

    def test_backup_failure_still_persists_private_status(self):
        calls = []
        def fake(args, **kwargs):
            calls.append(args)
            if args[:2] == ['git', 'clone']:
                Path(args[-1]).mkdir()
            code = 2 if args == ['python3', 'scripts/backup.py'] else 0
            return SimpleNamespace(returncode=code)
        self.assertEqual(execute(self.env, fake), 2)
        self.assertIn(['git', 'add', 'metadata', 'status'], calls)


if __name__ == '__main__':
    unittest.main()
