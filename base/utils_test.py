import unittest

from tf_serving_flask_app.base.utils import as_boolean


class TestUtils(unittest.TestCase):
    def test_valid_booleans(self):
        self.assertTrue(as_boolean(True))
        self.assertTrue(as_boolean('true'))
        self.assertTrue(as_boolean('t'))
        self.assertTrue(as_boolean('y'))
        self.assertTrue(as_boolean('yes'))
        self.assertTrue(as_boolean('on'))
        self.assertTrue(as_boolean('1'))

        self.assertFalse(as_boolean(False))
        self.assertFalse(as_boolean('false'))
        self.assertFalse(as_boolean('f'))
        self.assertFalse(as_boolean('false'))
        self.assertFalse(as_boolean('n'))
        self.assertFalse(as_boolean('no'))
        self.assertFalse(as_boolean('0'))

    def test_invalid_booleans(self):
        with self.assertRaises(AssertionError):
            as_boolean(1)

        with self.assertRaises(AssertionError):
            as_boolean(None)

        with self.assertRaises(ValueError):
            as_boolean('foo')


if __name__ == '__main__':
    unittest.main()
