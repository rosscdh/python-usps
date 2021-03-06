"""
Base implementation of USPS service wrapper
"""

import urllib, urllib2
from usps.utils import utf8urlencode, xmltodict, dicttoxml
from usps.errors import USPSXMLError

try:
    from xml.etree import ElementTree as ET
except ImportError:
    from elementtree import ElementTree as ET

import logging
logger = logging.getLogger('django.request')

class USPSService(object):
    """
    Base USPS Service Wrapper implementation
    """
    SERVICE_NAME = ''
    CHILD_XML_NAME = ''
    PARAMETERS = []
    
    @property
    def API(self):
        return self.SERVICE_NAME
        
    def __init__(self, url, user_id, password):
        self.url = url
        self.user_id = user_id
        self.password = password

    def submit_xml(self, xml):
        """
        submit XML to USPS
        @param xml: the xml to submit
        @return: the response element from USPS
        """
        data = {'XML':ET.tostring(xml),
                'API':self.API}

        response = urllib2.urlopen(self.url, utf8urlencode(data))

        root = ET.parse(response).getroot()
        if root.tag == 'Error':
            raise USPSXMLError(root)
        error = root.find('.//Error')
        if error is not None:
            raise USPSXMLError(error)
        return root
    
    def parse_xml(self, xml):
        """
        Parse the response from USPS into a dictionary
        @param xml: the xml to parse
        @return: a dictionary representing the XML response from USPS
        """
        items = list()
        for item in xml:#xml.findall(self.SERVICE_NAME+'Response'):
            items.append(xmltodict(item))
        return items
    
    def make_xml(self, data, user_id, password=None):
        """
        Transform the data provided to an XML fragment
        @param userid: the USPS API user id
        @param data: the data to serialize and send to USPS
        @return: an XML fragment representing data
        """
        root = ET.Element(self.SERVICE_NAME+'Request')
        root.attrib['USERID'] = user_id
        root.attrib['PASSWORD'] = password
        index = 0
        for data_dict in data:
            data_xml = dicttoxml(data_dict, self.CHILD_XML_NAME, self.PARAMETERS)
            data_xml.attrib['ID'] = str(index)
            root.append(data_xml)
            index += 1
        return root
    
    def execute(self,data, user_id=None, password=None):
        """
        Create XML from data dictionary, submit it to 
        the USPS API and parse the response
        
        @param user_id: a USPS user id
        @param data: the data to serialize and submit
        @return: the response from USPS as a dictionary
        """
        if user_id is None:
            user_id = self.user_id

        if password is None:
            password = self.password
            
        xml = self.make_xml(data, user_id, password)
        logger.debug(ET.tostring(xml, encoding='utf8', method='xml'))
        response = self.submit_xml(xml)
        logger.debug(ET.tostring(response, encoding='utf8', method='xml'))
        return self.parse_xml(response)