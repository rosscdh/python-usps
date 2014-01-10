# -*- coding: utf-8 -*-
"""
USPS Tracking Code Field Validator that can be used with django

Used to be based on: https://code.google.com/p/php-parcel-tracker/source/browse/carriers/usps.class.php?r=ecd3a1e9dfed7a2555b39178bf6bfd197040933e
But that was broken so based it on: https://github.com/franckverrot/activevalidators/blob/master/lib/active_model/validations/tracking_number_validator.rb
Thanks to the original contributors
"""
from django.forms import CharField, ValidationError

from itertools import cycle
import re


class InvalidTrackingNumber(ValidationError):
    message = 'The Tracking Code "{value}" is not valid'

    def __init__(self, value):
        self.message = self.message.format(value=value)
        super(InvalidTrackingNumber, self).__init__(self.message)


class USPSTrackingCodeField(CharField):
    original = None

    USS128_REGEX = r'^(\d{19,21})(\d)$'
    USS39_REGEX = r'^[a-zA-Z0-9]{2}(\d{8})(\d)US$'

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
        matches = self.get_matches(self.USS128_REGEX, tracking_code)
        if matches is None:
            return False

        current_value = matches[0]
        end_value = int(matches[1])

        checksum = self.usps_mod10(current_value[::-1])  # reverse the string in this case

        return checksum == end_value

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
        matches = self.get_matches(self.USS39_REGEX, tracking_code)

        if matches is None:
            return False

        current_value = matches[0]
        end_value = int(matches[1])

        return (end_value == self.usps_mod10(chars=current_value) or end_value == self.usps_mod11(chars=current_value))

    #
    # Calculate using the mod10 algorythm
    #
    def usps_mod10(self, chars):
        range_sum = self.weighted_sum(value=chars, weights=[3, 1])
        return (10 - range_sum % 10) % 10

    #
    # Calculate using the mod11 algorythm
    #
    def usps_mod11(self, chars):
        mod = self.weighted_sum(value=chars, weights=[8, 6, 4, 2, 3, 5, 9, 7]) % 11
        if mod == 0:
            return 5
        elif mod == 1:
            return 0
        else:
            return 11 - mod

    #
    # Extract matches from string based on provided
    # regex
    #
    def get_matches(self, regex, value):
        matches = re.match(regex, value)
        if matches is None:
            return None  # return None if there are no matches
        try:
            return matches.groups()
            # raise exception if this is busted
        except:
            raise InvalidTrackingNumber(self.original)

    #
    # Calculate the weighted sum based on the ruby validators
    #
    def weighted_sum(self, value, weights):
        """
        takes a string containing digits and calculates a checksum using the
        provided weight array
        """
        # digits = value.split('').map { |d| d.to_i }
        digits = map(int, str(value))
        num_digits = len(digits)

        # cycles the weight list if it's not long enough
        # get 2 lists of equal length
        # >>> digits
        # [2, 3, 7, 4, 4, 9, 1, 1, 0, 0, 0, 0, 3, 6, 2, 3, 1, 0, 7]
        # >>> weights
        # [3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3]
        # zip them up and return a new list of the digit multiplied by the weight
        #
        if len(weights) < num_digits:
            for w in cycle(weights):
                if len(weights) < num_digits:
                    weights.append(w)
                else:
                    break

        return sum([digit * weight for digit, weight in zip(digits, weights)])

    def clean(self, value):
        self.original = value
        tracking_code = ''.join(value.split())  # ensure no whitespace

        # if its not one of these
        if self.is_USS39(tracking_code=tracking_code) is False:
            # and not one of those
            if self.is_USS128(tracking_code=tracking_code) is False:
                # then its not a USPS tracking code I'm afraid
                raise InvalidTrackingNumber(self.original)
        return value
