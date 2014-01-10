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
            # loop over test vals
            values = self.value if type(self.value) in [list, tuple] else [self.value]
            for value in values:
                subject.clean(value=value)


class Django_USS128_TrackingCodeTest(BaseTrackingCode):
    subject = USPSTrackingCodeField
    value = ['7013 2630 0001 1944 7323', '70132630000013657033']

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