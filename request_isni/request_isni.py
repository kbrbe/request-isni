import requests
import csv
import os
from dotenv import load_dotenv
from datetime import date
import logging
import time
import xml.etree.ElementTree as ET
import urllib
import lib
from io import BytesIO
from optparse import OptionParser

NS_SRW = 'http://www.loc.gov/zing/srw/'


# -----------------------------------------------------------------------------
def checkArguments():

  parser = OptionParser(usage="usage: %prog [options]")
  parser.add_option('-i', '--input-folder', action='store', help='XML requests sent to the ISNI API are read from this folder')
  parser.add_option('-o', '--output-file', action='store', help='A list with results is stored in this CSV file')
  parser.add_option('-r', '--response-folder', action='store', help='The folder in which received responses are stored')
  parser.add_option('-u', '--url', action='store', help='The URL to which the request should be sent')
  (options, args) = parser.parse_args()

  #
  # Check if we got all required arguments
  #
  if( (not options.input_folder) or (not options.output_file) ):
    parser.print_help()
    exit(1)

  if not options.response_folder:
    options.response_folder = os.path.join(options.input_folder, 'responses')

  #
  # load environment variables from .env file
  #
  load_dotenv()

  if not options.url:
    options.url = os.getenv('ISNI_ATOM_URL')

  if options.url:
    return options
  else:
    print('No URL provided via commandline or environment file!')
    exit(1)

# -----------------------------------------------------------------------------
def main(inputFolder, outputFile, responseFolder, url):

  if not os.path.isdir(inputFolder):
    print(f'The provided inputFolder "{inputFolder}" is not a directory!')
    exit(1)

  with open(outputFile, 'w', encoding='utf-8', newline='') as outFile:
    outputWriter = csv.DictWriter(outFile, fieldnames=['KBRID', 'surname', 'forename', 'isniStatus', 'ISNI', 'PPN', 'SOURCE', 'comment'])
    outputWriter.writeheader()

    if not os.path.exists(responseFolder):
      os.makedirs(responseFolder)

    allFiles = os.listdir(inputFolder)
    allXMLFiles = []
    for inputFile in os.listdir(inputFolder):
      if inputFile.endswith('.xml'):
        allXMLFiles.append(inputFile)

    numberFiles = len(allFiles)
    numberXMLFiles = len(allXMLFiles)
    print(f'Found {numberFiles} files in directory from which {numberXMLFiles} are XML files.')

    for inputFile in allXMLFiles:

      inputData = None
      responseBytes = None
      responseText = None

      #
      # First step: check the request and extract data we need for the output: the KBRID
      #
      with open(os.path.join(inputFolder, inputFile), 'rb') as inFile:

        try:
          print(f'Process "{inputFile}" ...')

          inputData = lib.getISNIRequestData(ET.parse(inFile).getroot())
        except Exception as e:
          print(f'Error reading/parsing the input file "{inputFile}"')
          print(e)
          continue

      #
      # Second step: send the request to ISNI and parse the response
      #
      with open(os.path.join(inputFolder, inputFile), 'rb') as inFile, \
           open(os.path.join(responseFolder, f'response-{inputFile}'), 'w', encoding='utf-8') as responseFile:

        response = None
        try:
          # try to send one ISNI XML request to the server
          response = requests.post(url, data=inFile)

          # when everything was okay, save the response in case we have to lookup details later
          responseBytes = response.content

          if response.encoding is None:
            response.encoding = 'utf-8'
          responseText = response.text
          responseFile.write(responseText)

          # When the API did not return HTTP code 200 OK, but for example the error code 404 or 500
          # then raise an error (so we do not have to manually check if an error occurred,
          # instead we can handle the raised error using the except blocks below)
          response.raise_for_status()

        except requests.exceptions.Timeout:
          print(f'There was a timeout when sending "{inputFile}"')
        except requests.exceptions.TooManyRedirects:
          print(f'There were too many redirects for "{inputFile}"')
          continue
        except requests.exceptions.HTTPError as err:
          print(f'There was an HTTP response code which is not 200 for "{inputFile}"')
          print(err)
          print(responseText)
          continue
        except UnicodeEncodeError as err:
          print(err)
          print(f'There was an issue with the encoding of the ISNI server response, it should have been "{response.encoding}"')
          rawResponseFilename = os.path.join(responseFolder, f'response-raw-{inputFile}')
          with open(rawResponseFilename, 'wb') as responseBytes:
            responseBytes.write(response.content)
          continue
        except requests.exceptions.RequestException as err:  
          print(f'Something went wrong when trying to send a request for "{inputFile}"')
          print(err)
          continue

      #
      # Third step: combine data from the request and the response to append a row to our output CSV
      #
      try:
        # when everything was okay, parse the resulting XML and add information to the output file
        outputData = lib.parseResult(ET.fromstring(responseText))

        # write a combination of input data (the KBRID for which an ISNI was requested)
        # and output data (fields from the ISNI request response) to the output file
        outputData.update(inputData)
        outputWriter.writerow(outputData)
      except Exception as err:
        print(f'There was an error when adding a line to the output file "{outputFile}" based on request "{inputFile}"')
        print(err)


     
if __name__ == '__main__':
  args = checkArguments()
  main(args.input_folder, args.output_file, args.response_folder, args.url)
