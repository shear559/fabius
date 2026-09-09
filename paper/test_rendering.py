"""Regress TeX escaping at the HTML boundary without browser dependencies."""
import unittest
from build import math_safe

class MathEscaping(unittest.TestCase):
    def test_escaped_star_is_supported_mathjax_tex(self):
        self.assertEqual(math_safe(r'\(v^\*\)'), r'\(v^\ast \)')
        self.assertEqual(math_safe(r'\[x^{\*} < y\]'), r'\[x^{\ast } \lt  y\]')

    def test_normal_tex_and_prose_are_preserved(self):
        self.assertEqual(math_safe(r'\(x^*\) prose \*'), r'\(x^*\) prose \*')
        self.assertEqual(math_safe(r'\(a > b\)'), r'\(a \gt  b\)')

if __name__ == '__main__':
    unittest.main()
