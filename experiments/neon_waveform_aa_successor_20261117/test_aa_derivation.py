"""CPU geometry proof only; this never launches Godot or reads captured pixels."""
import math
import unittest


BAR = (12 / 255, 13 / 255, 17 / 255)
SAVED = (61 / 255, 220 / 255, 151 / 255)
WAVE = (.239, .863, .592)


def blend(dst, src, alpha):
    return tuple(d * (1 - alpha) + s * alpha for d, s in zip(dst, src))


def coverage(left, aa, pixel_x):
    return (pixel_x + .5 - (left - aa * .5)) / aa


def barycentric_alpha(point, vertices):
    # Independent interpolation in the actual two-triangle straight strip.
    (x, y) = point
    (x0, y0, a0), (x1, y1, a1), (x2, y2, a2) = vertices
    determinant = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    w0 = ((y1 - y2) * (x - x2) + (x2 - x1) * (y - y2)) / determinant
    w1 = ((y2 - y0) * (x - x2) + (x0 - x2) * (y - y2)) / determinant
    w2 = 1 - w0 - w1
    if min(w0, w1, w2) < -1e-12:
        return None
    return a0 * w0 + a1 * w1 + a2 * w2


def strip_alpha(left, aa, x, y):
    a = (left - aa / 2, 0, 0)
    b = (left + aa / 2, 0, 1)
    c = (left + aa / 2, 30, 1)
    d = (left - aa / 2, 30, 0)
    for triangle in ((a, b, c), (a, c, d)):
        alpha = barycentric_alpha((x, y), triangle)
        if alpha is not None:
            return alpha
    return None


class DerivationTests(unittest.TestCase):
    def test_closed_form_matches_triangle_interpolation(self):
        for left in (0, .1, 1 / 3, .5, .9, 559 + 1 / 3):
            for aa in (.5, 1, 2):
                for fraction in (0, .125, .25, .5, .75, .875, 1):
                    for y in (4.5, 14.5, 25.5):
                        x = left - aa / 2 + fraction * aa
                        self.assertAlmostEqual(strip_alpha(left, aa, x, y), fraction)

    def test_half_pixel_center_matters(self):
        self.assertAlmostEqual(coverage(10 + 1 / 3, 1, 10), 2 / 3)
        self.assertAlmostEqual(coverage(10.5, 1, 10), .5)
        self.assertAlmostEqual(coverage(10, 1, 10), 1)

    def test_integer_translation_invariant(self):
        for offset in (-200, 0, 500):
            self.assertAlmostEqual(coverage(10 + 1 / 3 + offset, 1, 10 + offset), 2 / 3)

    def test_opaque_border_prediction_is_not_aa_prediction(self):
        expected = blend(blend(BAR, SAVED, 2 / 3), WAVE, .85)
        opaque = blend(SAVED, WAVE, .85)
        self.assertGreater(abs(expected[1] - opaque[1]), .02)

    def test_missing_edge_transient_does_not_match(self):
        underlay = blend(BAR, SAVED, 2 / 3)
        expected = blend(underlay, WAVE, .85)
        self.assertGreater(min(abs(a - b) for a, b in zip(underlay, expected)), .02)

    def test_missing_interior_transient_does_not_match(self):
        underlay = blend(BAR, WAVE, .12)
        expected = blend(underlay, WAVE, .85)
        self.assertGreater(min(abs(a - b) for a, b in zip(underlay, expected)), .02)

    def test_outside_feather_is_not_silently_clamped(self):
        self.assertLess(coverage(10.75, 1, 9), 0)
        self.assertGreater(coverage(10.25, 1, 11), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
