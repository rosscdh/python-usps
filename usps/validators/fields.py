# -*- coding: utf-8 -*-
"""
Validator heplers that can be used with django
Credit: https://code.google.com/p/php-parcel-tracker/source/browse/carriers/usps.class.php?r=ecd3a1e9dfed7a2555b39178bf6bfd197040933e
"""
from django.forms import CharField, ValidationError

from math import ceil

class InvalidTrackingNumber(ValidationError):
    message = 'The Tracking Code entered is not valid'

    def __init__(self):
        super(InvalidTrackingNumber, self).__init__(self.message)


class USPSTrackingCodeField(CharField):
    tracking_code = None
    #
    # Validate a USPS tracking number based on USS Code 128 Subset C 20-digit barcode PIC (human
    # readable portion).
    # i.e. 70132630000013657033
    # @link http://www.usps.com/cpim/ftp/pubs/pub109.pdf (Publication 109. Extra Services Technical Guide, pg. 19)
    # @link http://www.usps.com/cpim/ftp/pubs/pub91.pdf (Publication 91. Confirmation Services Technical Guide pg. 38)
    # @param $trackingNumber string The tracking number to perform the test on.
    # @return boolean True if the passed number is a USS 128 shipment.
    #
    def is_USS128(self, tracking_code):
        # ensure its the correct length
        # and that the tracking_code IS numeric, ie its not uss128 if the code is not numeric
        if self.tracking_code_len not in [20, 22, 30] or self.tracking_code_is_numeric is False:
            return False

        value = str(tracking_code[:]) # duplicate the val as we make changes to it and ensure is an integer

        if self.tracking_code_len == 20:
            # Add service code to shortened number. This passes known test cases but need
            # to verify that this is always a correct assumption.
            value = '91%s' % value

        elif self.tracking_code_len == 30:
            # Truncate extra information
            value = value[8:30]

        # cast it as an int
        value = int(value)

        range_list = range(0, 21) # need a list of 0..20 (thus 21 for pythons range)
        range_list.reverse()  # reverse the list as we need it from highest to lowest

        reversed_value = value.__str__()[::-1] # reverse the value as per https://github.com/franckverrot/activevalidators/blob/master/lib/active_model/validations/tracking_number_validator.rb

        range_sum = self.range_sum(current_value=reversed_value, range_list=range_list, weights=[3, 1])

        checksum = (ceil(range_sum / 10) * 10) - range_sum

        return int(abs(checksum)) == int(value.__str__()[21])

    #
    # Validate a USPS tracking number based on a USS Code 39 Barcode, this uses the MOD 11
    # check character calculation for validating both domestic and international mail. The
    # i.e. EJ958083578US
    # MOD 10 check may be used for domestic mail but is not needed in this scenario.
    # @link http://www.usps.com/cpim/ftp/pubs/pub97.pdf (Publication 97. Express Mail Manifesting Technical Guide, pg. 64)
    # @param $trackingNumber string The tracking number to perform the test on.
    # @return boolean True if the passed number is a USS 39 tracking number.
    #
    def is_USS39(self, tracking_code):
        value = tracking_code[:] # duplicate the val as we make changes to it
        if self.tracking_code_len not in [13] or type(value[0:2]) is not str or type(value[-2:]) is not str:
            return False

        value = value[2:-2]  # drop the first 2 and last 2 str elements "EJ" and "US"

        range_sum = self.range_sum(current_value=value, range_list=range(0, 8), weights=[8, 6, 4, 2, 3, 5, 9, 7])

        # get a check_digit to calculate teh checksum against
        check_digit = range_sum % 11

        if check_digit == 0:
            checksum = 5
        elif check_digit == 1:
            checksum = 0
        else:
            checksum = 11 - check_digit

        return checksum == int(value[8])

    def range_sum(self, current_value, range_list, weights):
        """
        calculate a range_sum which is used to calcukate checksum
        done by passing in a list to loop over and then calculate weights
        against.
        """
        range_sum = 0
        num_weights = len(weights)

        for i in range_list:
            try:
                range_sum += (weights[i % num_weights] * int(current_value.__str__()[i]))
            except:
                raise InvalidTrackingNumber

        return range_sum

    def clean(self, value):
        value = ''.join(value.split())  # ensure no whitespace
        self.tracking_code = value  # store it for use in range_sum
        self.tracking_code_len = len(value)  # get the length of the string
        self.tracking_code_is_numeric = value.isdigit()  # evalute is alpha-numericy

        # if its not one of these
        if self.is_USS39(tracking_code=value) is False:
            # and not one of those
            if self.is_USS128(tracking_code=value) is False:
                # then its not a USPS tracking code I'm afraid
                raise InvalidTrackingNumber
        return value