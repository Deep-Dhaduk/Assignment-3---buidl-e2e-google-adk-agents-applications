import unittest

from pricing import average_price, calculate_total


class PricingTests(unittest.TestCase):
    def test_quantity(self):
        self.assertEqual(calculate_total(1200, 3), 3600)

    def test_empty_cart(self):
        self.assertEqual(average_price([]), 0)

    def test_negative_quantity(self):
        with self.assertRaises(ValueError):
            calculate_total(1200, -2)

    def test_average(self):
        self.assertEqual(average_price([100, 200]), 150)


if __name__ == "__main__":
    unittest.main()
