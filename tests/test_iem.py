import unittest
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)) + os.sep + "..")

from sense.surface import I2EM

class Test_IEM(unittest.TestCase):
    def setUp(self):
        self.eps = 4.+0.j
        self.theta = 0.5
        self.f = 6.
        self.s = 0.01
        self.l = 0.1

    def tearDown(self):
        pass
    
    def test_init(self):
        O = I2EM(self.f, self.eps, self.s, self.l, self.theta, auto=False)
        self.assertEqual(O.eps, self.eps)
        self.assertEqual(O.ks, O.k*O.sig)
        self.assertEqual(O.kl, O.k*O.l)

    def test_scat(self):
        O = I2EM(self.f, self.eps, self.s, self.l, self.theta, auto=False)

if __name__ == '__main__':
    unittest.main()
