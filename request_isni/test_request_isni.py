import importlib
import io
import sys
import shutil
import os
import csv
import unittest
import tempfile
import requests
import lib
import xml.etree.ElementTree as ET
from unittest.mock import patch, MagicMock
import request_isni

# Don't show the traceback of an AssertionError, because the AssertionError already says what the issue is!
__unittest = True

class TestRequestISNI(unittest.TestCase):

  # ---------------------------------------------------------------------------
  def setUp(self):
    self.tempOutput = os.path.join(tempfile.gettempdir(), 'output.csv')
    self.responseFolder = os.path.join(tempfile.gettempdir(), 'responses')

  # ---------------------------------------------------------------------------
  def tearDown(self):
    if os.path.isfile(self.tempOutput):
      os.remove(self.tempOutput)

    if os.path.exists(self.responseFolder):
      shutil.rmtree(self.responseFolder)
    

  # ---------------------------------------------------------------------------
  def testDoctests(self):
    """Test doctest unit tests of lib.py so it will be counted when computing the test coverage"""
    import doctest
    doctest.testmod(lib)

  # ---------------------------------------------------------------------------
  def testIncorrectInputFolder(self):
    """This function tests if the program stops if an invalid input folder is given."""
    with self.assertRaises(SystemExit):
      request_isni.main('folder-which-does-not-exist', 'outputFile.csv', 'folder-which-does-not-exist-responses', 'myURL')

  # ---------------------------------------------------------------------------
  @unittest.mock.patch('request_isni.requests.post')
  def testOutputGenerated(self, mock_request):
    """This function tests if a CSV with correct values is created based on a response from a mock API."""

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '<responseRecord><ISNIAssigned><isniUnformatted>0000000000000001</isniUnformatted><ISNIMetadata><sources><codeOfSource>BNF</codeOfSource><sourceIdentifier>123</sourceIdentifier></sources></ISNIMetadata></ISNIAssigned></responseRecord>'
    mock_request.return_value = mock_response

    request_isni.main('testResources/oneXMLFile', self.tempOutput, self.responseFolder, 'myURL')

    with open(self.tempOutput, 'r') as outFile:
      resultReader = csv.reader(outFile)
      result = list(resultReader)

      expectedResult = [['KBRID', 'surname', 'forename', 'isniStatus', 'ISNI', 'PPN', 'SOURCE', 'comment'], ['123', 'Doe', 'John', 'confidentMatch', '0000 0000 0000 0001', '', '', '']]
      self.assertCountEqual(result, expectedResult, msg='Incorrect CSV output was produced')
      

  # ---------------------------------------------------------------------------
  @unittest.mock.patch('request_isni.requests.post')
  def testHTTPError(self, mock_request):
    """This function tests if an expected error messages is provided if the server response was not 200."""

    # preserving the original raise_for_status function by using the model of Response
    mock_response = requests.models.Response()

    # manually set the error values
    mock_response.status_code = 404
    mock_request.return_value = mock_response

    # capture print output from the script
    capturedOutput = io.StringIO()
    sys.stdout = capturedOutput

    # call the script
    request_isni.main('testResources/oneXMLFile', self.tempOutput, self.responseFolder, 'myURL')
    sys.stdout = sys.__stdout__

    expected = 'Found 1 files in directory from which 1 are XML files.\nProcess "file1.xml" ...\nThere was an HTTP response code which is not 200 for "file1.xml"\n404 Client Error: None for url: None\n\n'

    # check if what was printed was what was expected
    self.assertEqual(capturedOutput.getvalue(),
                     expected,
                     msg='Wrong error message')

if __name__ == '__main__':
  unittest.main()
