"""
Track and Confirm class
"""
from usps.api.base import USPSService

try:
    from xml.etree import ElementTree as ET
except ImportError:
    from elementtree import ElementTree as ET


class TrackConfirm(USPSService):
    """
    Basic Tracking Confirmation returns basic summary of events
    """
    SERVICE_NAME = 'Track'
    CHILD_XML_NAME = 'TrackID'
    API = 'TrackV2'
    
    def make_xml(self, data, user_id, password):
          
        root = ET.Element(self.SERVICE_NAME+'Request')
        root.attrib['USERID'] = user_id
        root.attrib['PASSWORD'] = password
        
        for data_dict in data:
            track_id = data_dict.get('ID', False)
            if track_id:
                data_xml = ET.Element('TrackID')
                data_xml.attrib['ID'] = str(track_id)
                root.append(data_xml) 

        return root
    


class TrackConfirmWithFields(TrackConfirm):
    """
    Tracking Confirmation with Field details
    refer to: https://www.usps.com/business/web-tools-apis/track-and-confirm-v1-3a.htm#_Toc275424093
    """
    SERVICE_NAME = 'TrackField'