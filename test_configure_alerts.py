import io
import unittest
from unittest.mock import patch

from configure_alerts import main


class WatchdogCheckTests(unittest.TestCase):
    def check(self, healthy):
        response = io.BytesIO(b'{"healthy":' + (b'true' if healthy else b'false') + b'}')
        response.status = 200
        with patch.dict('os.environ', {'CHECK_ONLY': 'true', 'BACKUP_CALLBACK_SECRET': 'fixture'}), \
                patch('urllib.request.urlopen', return_value=response):
            main()

    def test_http_success_does_not_hide_unhealthy_result(self):
        with self.assertRaises(SystemExit) as result:
            self.check(False)
        self.assertEqual(result.exception.code, 2)

    def test_healthy_result_passes(self):
        self.check(True)


if __name__ == '__main__':
    unittest.main()
