import unittest
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)) + os.sep + "..")

from sense.surface import I2EM
import numpy as np

class Test_IEM(unittest.TestCase):
    def setUp(self):
        self.eps = 4.+0.j
        self.theta = 0.5
        self.f = 6.
        self.s = 0.01
        self.l = 0.1
        self.thetas = 0.5
        self.phis = np.pi

    def tearDown(self):
        pass
    
    def test_init(self):
        O = I2EM(self.f, self.eps, self.s, self.l, self.theta, self.thetas, self.phis)
        self.assertEqual(O.eps, self.eps)
        self.assertEqual(O.ks, O.k*O.s)
        self.assertEqual(O.kl, O.k*O.l)


if __name__ == '__main__':
    unittest.main()
