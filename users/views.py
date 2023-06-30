from django.shortcuts import render

# Create your views here.
import json
from django.middleware.csrf import get_token
from django.http import JsonResponse
from cas import CASClient
from rest_framework.exceptions import AuthenticationFailed, ParseError

import datahub.pipelines.hub as pipe
import sussy_crudproject.settings as settings
from datahub.pipelines.hub import ReferenceData
from datahub.pipelines.hub import ApiResponse
from users.authentification import verify_jwt
from users.authentification import create_jwt
import sussy_crudproject.settings as settings

"""NOTE:
  actions shouldnt implement a try catch block, that block should be specific to each different data pipelines
"""

def csrfToken(request):
  return JsonResponse({'csrfToken': get_token(request)})

"""_summary_
@params request: django request object containing a cas ticket
@description API route api/cas/ that validates cas ticket and create a custom rest-framework jwt
@returns a Django response following ./restapiresponse.json pattern including a  jwt token if the user is authenticated
"""
def cas_validation(request):
  req = json.loads(request.body)
  ticket = req.get('ticket')
  service = request.build_absolute_uri()
  service = 'http://localhost:8000'
  client = CASClient(server_url=settings.CAS_SERVER_URL, service_url=service, version=3)
  username, attributes, pgtiou = client.verify_ticket(ticket)
  if not username:
    return JsonResponse({"error": "Invalid ticket"}, status=400)
  # User is authenticated, issue JWT
  reference = pipe.fetch(ReferenceData(username=username))
  if reference is None:
    return ApiResponse(401, "Authentification failed", None)
  else:
    token = create_jwt(username, reference.reference.role)
    response = JsonResponse({"status": 200, "jwt": token}, status=200)
    return response

"""_summary_
@params request: django request object containting a jwt token
@description API route api/auth/ that validates jwt token
@returns a django response following ./restapiresponse.json with status 200 if the token is valid, 401 if not
"""
def authenticate(request):
  req = json.loads(request.body)
  token = req.get('jwt')
  try:
    payload = verify_jwt(token)
  except AuthenticationFailed:
    return ApiResponse(401, "Authentification failed", None).JsonResponse()
  except ParseError:
    return ApiResponse(400, "Invalid JWT token", None).JsonResponse()
  return ApiResponse(200, "Authentification success!", None).JsonResponse()