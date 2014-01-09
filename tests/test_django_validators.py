# -*- coding: utf-8 -*-
import unittest

from usps.validators import USPSTrackingCodeField, InvalidTrackingNumber


class BaseTrackingCode(unittest.TestCase):
    subject = None
    value = None

    def setUp(self):
        super(BaseTrackingCode, self).setUp()

    def test_is_valid(self):
        if self.subject is not None:
            subject = self.subject()
            subject.clean(value=self.value)


class Django_USS128_TrackingCodeTest(BaseTrackingCode):
    subject = USPSTrackingCodeField
    value = '70132630000013657033'

    def test_invalid(self):
        value = 'this_is_wrong'
        subject = self.subject()
        with self.assertRaises(InvalidTrackingNumber):
            subject.clean(value=value)


class Django_USS39_TrackingCodeTest(BaseTrackingCode):
    subject = USPSTrackingCodeField
    value = 'EJ958083578US'

    def test_invalid(self):
        value = 'this_is_wrong'
        subject = self.subject()
        with self.assertRaises(InvalidTrackingNumber):
            subject.clean(value=value)

if __name__ == '__main__':
    unittest.main()