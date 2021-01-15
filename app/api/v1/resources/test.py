"""
DRS healthcheck resource module.
Copyright (c) 2018-2020 Qualcomm Technologies, Inc.
All rights reserved.
Redistribution and use in source and binary forms, with or without modification, are permitted (subject to the limitations in the disclaimer below) provided that the following conditions are met:

    Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
    Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
    Neither the name of Qualcomm Technologies, Inc. nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
    The origin of this software must not be misrepresented; you must not claim that you wrote the original software. If you use this software in a product, an acknowledgment is required by displaying the trademark/log as per the details provided here: https://www.qualcomm.com/documents/dirbs-logo-and-brand-guidelines
    Altered source versions must be plainly marked as such, and must not be misrepresented as being the original software.
    This notice may not be removed or altered from any source distribution.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
import json
import uuid

from pprint import pprint

from flask import Response, request
from flask_apispec import marshal_with, doc, MethodResource
from flask_restful import Resource
from flask_babel import lazy_gettext as _


from app import app, db
from app.api.v1.models.regdetails import RegDetails
from app.api.v1.schema.ussd import RegistrationDetailsSchema

from app.api.v1.helpers.response import MIME_TYPES, CODES
from app.api.v1.helpers.utilities import Utilities

from app.metadata import version, db_schema_version
from app.api.v1.schema.version import VersionSchema

from app.api.v1.helpers.key_cloak import Key_cloak
from app.api.v1.helpers.sms import Jasmin

from app.api.v1.schema.reviewer import ErrorResponse
from marshmallow import Schema, fields, validates, ValidationError, post_dump, validate, pre_dump


class Send(MethodResource):
    """Class for handling version api resources."""

    def get(self):
        """GET method handler."""
        return Response(json.dumps(
            VersionSchema().dump(dict(
                version=version,
                db_schema_version=db_schema_version
            )).data))

    def post(self):
        print("Are we in the send API Call")
        sender = '03337372337'
        network = 'ufone-smpp'
        message = "This is the test message to be send to the user"
        jasmin_send_response = Jasmin.send(sender, network, message)
        print(jasmin_send_response)
        return Response(json.dumps(
            VersionSchema().dump(dict(
                version=version,
                db_schema_version=db_schema_version
            )).data))


class SendBatchTest(MethodResource):
    """Class for handling version api resources."""

    def get(self):
        """GET method handler."""
        return Response(json.dumps(
            VersionSchema().dump(dict(
                version=version,
                db_schema_version=db_schema_version
            )).data))

    def post(self):
        print("Are we in the Send Batch Post call")

        messages_list = []
        messages = {
            'from': 'ikram',
            'to': '03337372337',
            'content': 'This is the first test message to be send to the user'
        }
        messages_list.append(messages.copy())

        jasmin_send_response = Jasmin.send_batch(messages_list, network='ufone')
        print(jasmin_send_response)
        return Response(json.dumps(
            VersionSchema().dump(dict(
                version=version,
                db_schema_version=db_schema_version
            )).data))