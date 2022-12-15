#
# (c) 2022 Sven Lieber
# KBR Brussels
#
import xml.etree.ElementTree as ET

# -----------------------------------------------------------------------------
def formatISNI(isni):
  """This function formats ISNI identifiers by adding spaces if needed.

  >>> formatISNI("0001000100010001")
  '0001 0001 0001 0001'
  """
  isni = isni.strip()
  return isni[0:4] + ' ' + isni[4:8] + ' ' + isni[8:12] + ' ' + isni[12:16]

# -----------------------------------------------------------------------------
def parseResult(responseRecord):
  """This function parses an ISNI result record and extracts data.

  ------------------------------------------------------------
  # CASE CHAPTER 4: CONFIDENT MATCH
  When match is 100%

  If the ISNI matching found a confident match, we report the resulting ISNI identifier that we received.
  >>> xml1 = ET.fromstring('<responseRecord><ISNIAssigned><isniUnformatted>0000000000000001</isniUnformatted><ISNIMetadata><sources><codeOfSource>BNF</codeOfSource><sourceIdentifier>123</sourceIdentifier></sources></ISNIMetadata></ISNIAssigned></responseRecord>')
  >>> parseResult(xml1)
  {'isniStatus': 'confidentMatch', 'ISNI': '0000 0000 0000 0001', 'PPN': '', 'SOURCE': '', 'comment': ''}

  ------------------------------------------------------------
  # CASE CHAPTER 5: POSSIBLE MATCH (NoISNI)
  When match is betwen 060.00 and 085.00

  If the ISNI matching found a possible match, an ISNI-internal PPN identifier is returned which we add to the result
  >>> xml2 = ET.fromstring('<responseRecord><noISNI><possibleMatch><PPN>123</PPN><evaluationScore>70.00</evaluationScore><source>BNF#PERSON</source><mergeInstruction>P</mergeInstruction></possibleMatch></noISNI></responseRecord>')
  >>> parseResult(xml2)
  {'isniStatus': 'possibleMatch', 'ISNI': '', 'PPN': '123', 'SOURCE': 'BNF#PERSON', 'comment': ''}

  ------------------------------------------------------------
  # CASE CHAPTER 6: POSSIBLE MATCH CANNOT BE ASSIGNED (NoISNI)
  When a confident match is found, but the matching ISNI record is linked to another ISNI record

  >>> xml3 = ET.fromstring('<responseRecord><noISNI><PPN>123</PPN><reason>possible match cannot be assigned</reason><possibleMatch><PPN>456</PPN><evaluationScore>70.00</evaluationScore><source>BNF#PERSON</source><mergeInstruction>P</mergeInstruction></possibleMatch></noISNI></responseRecord>')
  >>> parseResult(xml3)
  {'isniStatus': 'possibleMatchCannotBeAssigned', 'ISNI': '', 'PPN': '456', 'SOURCE': 'BNF#PERSON', 'comment': ''}

  ------------------------------------------------------------
  # CASE CHAPTER 7: POSSIBLE MATCH (YOUR NAME IS ALREADY IN ISNI WITH ANOTHER ID)
  When a match was found, but the matching ISNI record already links to another of our local identifiers  

  For example, we sent a request to get an ISNI for KBRID 123, ISNI found a match, but that match already links to KBRID 456
  >>> xml4 = ET.fromstring('<responseRecord><noISNI><possibleMatch><PPN>456</PPN><evaluationScore>95.00</evaluationScore><source>KBR#PERSON</source><mergeInstruction>P</mergeInstruction></possibleMatch></noISNI></responseRecord>')
  >>> parseResult(xml4)
  {'isniStatus': 'possibleMatchDuplicateKBRID', 'ISNI': '', 'PPN': '456', 'SOURCE': 'KBR#PERSON', 'comment': ''}

  # CASE 26.2 Response NoISNI (Data not accepted / no reason given)
  >>> xml5 = ET.fromstring('<responseRecord><information>data not accepted</information><noISNI><reason>no match initial database</reason></noISNI></responseRecord>')
  >>> parseResult(xml5)
  {'isniStatus': 'noMatch', 'ISNI': '', 'PPN': '', 'SOURCE': '', 'comment': 'no match initial database'}

  # CASE 26.4 Response NoISNI (invalid data)
  >>> xml6 = ET.fromstring('<responseRecord><information>data not accepted</information><noISNI><reason>invalid data</reason><information>More info</information></noISNI></responseRecord>')
  >>> parseResult(xml6)
  {'isniStatus': 'noMatch', 'ISNI': '', 'PPN': '', 'SOURCE': '', 'comment': 'invalid data, More info'}
  
  """
  result = {'isniStatus': '', 'ISNI': '', 'PPN': '', 'SOURCE': '', 'comment': ''}
  if(responseRecord.tag == 'responseRecord'):
    
    isniAssigned = responseRecord.find('ISNIAssigned')

    result['comment'] = ''
    # There was a confident match and an ISNI identifier was returned
    if isniAssigned is not None:
      result['isniStatus'] = 'confidentMatch'
      result['ISNI'] = formatISNI(isniAssigned.find('isniUnformatted').text)
    else:

      # There should be noISNI indicating one of three cases
      isniNotAssigned = responseRecord.find('noISNI')
      if isniNotAssigned is not None:

        source = isniNotAssigned.find('possibleMatch/source')
        if source is not None:
          result['SOURCE'] = source.text
          # If we find a PPN as direct child there is a linked ISNI
          linkedISNIRecord = isniNotAssigned.find('PPN')
          if linkedISNIRecord is not None:
            result['isniStatus'] = 'possibleMatchCannotBeAssigned'
            result['PPN'] = isniNotAssigned.find('possibleMatch/PPN').text

          # It is a regular possible match or a possible match but with duplicate KBRID
          else:
            otherKBRRecord = True if isniNotAssigned.find('possibleMatch/source').text.startswith('KBR') else False
            if otherKBRRecord:
              result['isniStatus'] = 'possibleMatchDuplicateKBRID'
              result['PPN'] = isniNotAssigned.find('possibleMatch/PPN').text
            else:
              result['isniStatus'] = 'possibleMatch'
              result['PPN'] = isniNotAssigned.find('possibleMatch/PPN').text
 

        # There is no source given, probably no match found
        else:
          result['isniStatus'] = 'noMatch'
          reason = isniNotAssigned.find('reason')
          if reason is not None:
            result['comment'] = reason.text
          else:
            result['comment'] = 'No reason provided'

          # According to 26.4 there might be more info given if the reason is 'invalid data'
          # let's also add the additional info
          moreInfo = isniNotAssigned.find('information')
          if moreInfo is not None:
            result['comment'] = result['comment'] + ', ' + moreInfo.text

         
      # The record was no confident match and no 'NoISNI', what is it?
      else:
        print('This should not happen, unknown record structure:')
        print(ET.tostring(responseRecord, encoding='utf-8', method='xml'))
     
  return result

# -----------------------------------------------------------------------------
def getISNIRequestData(request):
  """This function extracts the KBRID from an ISNI request.

  >>> xml1 = ET.fromstring('<Request><identityInformation><requestorIdentifierOfIdentity><identifier>123</identifier></requestorIdentifierOfIdentity><identity><personOrFiction><personalName><surname>Doe</surname><forename>John</forename></personalName></personOrFiction></identity></identityInformation></Request>')
  >>> getISNIRequestData(xml1)
  {'KBRID': '123', 'surname': 'Doe', 'forename': 'John'}

  >>> xml2 = ET.fromstring('<myXML></myXML>')
  >>> getISNIRequestData(xml2)
  Traceback (most recent call last):
   ...
  Exception: Input is not an ISNI request
  """
  result = {'KBRID': '', 'surname': '', 'forename': ''}
  if request.tag == 'Request':
    result['KBRID'] = request.find('identityInformation/requestorIdentifierOfIdentity/identifier').text
    result['surname'] = request.find('identityInformation/identity/personOrFiction/personalName/surname').text
    result['forename'] = request.find('identityInformation/identity/personOrFiction/personalName/forename').text
  else:
    raise Exception('Input is not an ISNI request')

  return result
  
