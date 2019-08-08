#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

import dateutil.parser
import dateutil.tz

from girder.constants import AccessType
from girder.models.model_base import ValidationException
from girder.models.collection import Collection
from girder.models.folder import Folder
from girder.models.user import User


def getAssetsFolder(challenge, user, testAccess=True):
    """
    Get the Assets folder for a given challenge, creating one if it does not already exist.

    Ensures the specified user has read access on the folder if it already exists.

    :param challenge: The challenge.
    :type challenge: dict
    :param user: The user requesting the assets folder info.
    :type user: dict
    :param testAccess: Whether to verify that the user has read access to the
        folder.
    :type testAccess: bool
    :returns: The assets folder.
    """
    collection = Collection().load(
        challenge['collectionId'], force=True)

    if user is None and challenge['creatorId']:
        user = User().load(
            challenge['creatorId'], force=True)

    folder = Folder().createFolder(
        parentType='collection', parent=collection,
        name='Assets', creator=user, reuseExisting=True,
        description='Assets related to this challenge.')

    if testAccess:
        Folder().requireAccess(folder, user=user, level=AccessType.READ)

    return folder


def validateDate(date, field):
    """Convert datetime objects or ISO 8601-formatted strings to datetime objects in UTC."""
    date = str(date).strip()
    try:
        date = dateutil.parser.parse(date)
        if date.tzinfo is None:
            date = date.replace(tzinfo=dateutil.tz.tzutc())
    except ValueError:
        raise ValidationException('Invalid date format.', field=field)
    return date
