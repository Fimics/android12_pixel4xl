"""Utility class for sending requests to BonD, adding and controlling bots."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
import requests

from datetime import datetime
from oauth2client.client import GoogleCredentials


_BOND_API_URL = 'https://bond-pa.sandbox.googleapis.com'
_HANGOUTS_API_URL = 'https://preprod-hangouts.googleapis.com/hangouts/v1_meetings/'
_MEETINGS_API_URL = 'https://preprod-meetings.sandbox.googleapis.com'

_TOKEN_TTL_SECONDS = 3500

# See https://crbug.com/874835 for details on the credentials files.
_SERVICE_CREDS_FILE = '/creds/service_accounts/bond_service_account.json'


class BondHttpApi(object):
  """Utility class for sending requests to BonD for bots."""

  def __init__(self):
    self._last_token_request_time = None
    self._last_token = None

  def GetAvailableWorkers(self):
    """Gets the number of available workers for a conference."""
    token = self._GetAccessToken()
    resp = requests.get(
        '%s/v1/workers:count' % _BOND_API_URL,
        headers={
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % token
        })
    return json.loads(resp.text)["numOfAvailableWorkers"]

  def CreateConference(self):
    """Creates a conference.

    Returns:
      The meeting code of the created conference.
    """
    token = self._GetAccessToken()

    request_data = {
      'conference_type': 'THOR',
      'backend_options': {
        'mesi_apiary_url': _HANGOUTS_API_URL,
        'mas_one_platform_url': _MEETINGS_API_URL
      },
    }

    resp = requests.post(
        '%s/v1/conferences:create' % _BOND_API_URL,
        headers={
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % token,
        },
        data=json.dumps(request_data))
    json_response = json.loads(resp.text)
    logging.info("CreateConference response: %s", json_response)
    return json_response["conference"]["conferenceCode"]

  def ExecuteScript(self, script, meeting_code):
    """Executes the specified script.

    Args:
      script: Script to execute.
      meeting_code: The meeting to execute the script for.

    Returns:
      RunScriptRequest denoting failure or success of the request.
    """
    token = self._GetAccessToken()

    request_data = {
      'script': script,
      'conference': {
        'conference_code': meeting_code
      }
     }

    resp = requests.post(
        '%s/v1/conference/%s/script' % (_BOND_API_URL, meeting_code),
        headers={
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % token,
        },
        data=json.dumps(request_data))

    json_response = json.loads(resp.text)
    logging.info("ExecuteScript response: %s", json_response)
    return json_response['success']


  def AddBotsRequest(self,
                     meeting_code,
                     number_of_bots,
                     ttl_secs,
                     send_fps=24,
                     requested_layout='BRADY_BUNCH_4_4',
                     allow_vp9=True,
                     send_vp9=True):
    """Adds a number of bots to a meeting for a specified period of time.

    Args:
      meeting_code: The meeting to join.
      number_of_bots: The number of bots to add to the meeting.
      ttl_secs: The time in seconds that the bots will stay in the meeting after
        joining.
      send_fps: FPS the bots are sending.
      requested_layout: The type of layout the bots are requesting. Valid values
        include CLASSIC, BRADY_BUNCH_4_4 and BRADY_BUNCH_7_7.
      allow_vp9: If set, VP9 will be negotiated for devices where support is
        available. This only activates receiving VP9. See `send_vp9` for sending
      send_vp9: If set, VP9 will be preferred over VP8 when sending.
        `allow_vp9` must also be set for VP9 to be negotiated.

    Returns:
      List of IDs of the started bots.
    """
    # Not allowing VP9, but sending it is an invalid combination.
    assert(allow_vp9 or not send_vp9)
    token = self._GetAccessToken()

    request_data = {
      'num_of_bots': number_of_bots,
      'ttl_secs': ttl_secs,
      'video_call_options': {
        'allow_vp9': allow_vp9,
        'send_vp9': send_vp9,
      },
      'media_options': {
        'audio_file_path': "audio_32bit_48k_stereo.raw",
        'mute_audio': True,
        'video_fps': send_fps,
        'mute_video': False,
        'requested_layout': requested_layout,
      },
      'backend_options': {
        'mesi_apiary_url': _HANGOUTS_API_URL,
        'mas_one_platform_url': _MEETINGS_API_URL
      },
      'conference': {
        'conference_code': meeting_code
      },
      'bot_type': "MEETINGS",
      'use_random_video_file_for_playback': True
    }

    resp = requests.post(
        '%s/v1/conference/%s/bots:add' % (_BOND_API_URL, meeting_code),
        headers={
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % token
        },
        data=json.dumps(request_data))

    json_response = json.loads(resp.text)
    logging.info("AddBotsRequest response: %s", json_response)
    return json_response["botIds"]

  def _GetAccessToken(self):
    if self._last_token is None or self._CheckTokenExpired():
      credentials = self._CreateApiCredentials()
      scope = 'https://www.googleapis.com/auth/meetings'
      credentials = credentials.create_scoped(scope)
      self._last_token_request_time = datetime.now()
      self._last_token = credentials.get_access_token().access_token
    return self._last_token

  def _CreateApiCredentials(self):
    return GoogleCredentials.from_stream(_SERVICE_CREDS_FILE)

  def _CheckTokenExpired(self):
    elapsed = datetime.now() - self._last_token_request_time
    return elapsed.total_seconds() > _TOKEN_TTL_SECONDS
