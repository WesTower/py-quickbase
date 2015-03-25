import os
import unittest

import quickbase



class TestConnect(unittest.TestCase):
    def test_connect(self):
        conn = quickbase.connect(url=os.getenv('QUICKBASE_URL'),
                                 username=os.getenv('QUICKBASE_USERNAME'),
                                 password=os.getenv('QUICKBASE_PASSWORD'))
        self.assertNotEqual(conn, None)
