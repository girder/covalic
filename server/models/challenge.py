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

import datetime

from girder.constants import AccessType
from girder.models.model_base import AccessControlledModel, ValidationException
from girder.utility.progress import noProgress
from girder.plugins.covalic.utility import validateDate


class Challenge(AccessControlledModel):
    def initialize(self):
        self.name = 'challenge_challenge'
        self.ensureIndices(('collectionId', 'name', 'startDate', 'endDate'))
        self.ensureTextIndex({
            'name': 10,
            'description': 1
        })

        self.exposeFields(level=AccessType.READ, fields={
            '_id', 'creatorId', 'collectionId', 'name', 'description',
            'instructions', 'organizers', 'startDate', 'endDate', 'public',
            'thumbnails', 'thumbnailSourceId'})

    def list(self, user=None, limit=50, offset=0, sort=None, filters=None):
        """
        List a page of challenges.
        """
        cursor = self.find(filters or {}, limit=0, sort=sort)

        for r in self.filterResultsByPermission(cursor=cursor, user=user,
                                                level=AccessType.READ,
                                                limit=limit, offset=offset):
            yield r

    def subtreeCount(self, challenge):
        """
        Count up the recursive size of the challenge. This sums the size of
        each individual phase, then adds 1 for the challenge itself.
        """
        count = 1

        phases = self.model('phase', 'covalic').find({
            'challengeId': challenge['_id']
        }, fields=(), limit=0)
        for phase in phases:
            count += self.model('phase', 'covalic').subtreeCount(phase)

        return count

    def validate(self, doc):
        doc['name'] = doc['name'].strip()
        if doc.get('description'):
            doc['description'] = doc['description'].strip()
        if doc.get('instructions'):
            doc['instructions'] = doc['instructions'].strip()

        if not doc['name']:
            raise ValidationException(
                'Challenge name must not be empty.', 'name')

        # Ensure unique name for the collection
        q = {
            'name': doc['name']
        }
        if '_id' in doc:
            q['_id'] = {'$ne': doc['_id']}
        duplicate = self.findOne(q, fields=['_id'])
        if duplicate is not None:
            raise ValidationException('A challenge with that name already '
                                      'exists.', 'name')

        if doc.get('startDate'):
            doc['startDate'] = validateDate(doc['startDate'], 'startDate')
        if doc.get('endDate'):
            doc['endDate'] = validateDate(doc['endDate'], 'endDate')

        # Check that dates are in a sensible order
        if doc.get('startDate') and doc.get('endDate'):
            if doc['startDate'] >= doc['endDate']:
                raise ValidationException('Invalid start and end dates.',
                                          field='startDate')

        return doc

    def remove(self, challenge, progress=noProgress):
        # Remove all phases for this challenge
        phases = self.model('phase', 'covalic').find({
            'challengeId': challenge['_id']
        }, limit=0)
        for phase in phases:
            self.model('phase', 'covalic').remove(phase, progress=progress)
        phases.close()

        AccessControlledModel.remove(self, challenge)

        progress.update(increment=1,
                        message='Deleted challenge ' + challenge['name'])

    def createChallenge(self, name, creator, description='', instructions='',
                        public=True, organizers='', startDate=None,
                        endDate=None):
        if not name.strip():
            # pre-validate this since we have to create a collection first
            # with the same name.
            raise ValidationException(
                'You must provide a name for your challenge.', field='name')

        collection = self.model('collection').findOne({
            'name': name
        })

        if collection is None:
            collection = self.model('collection').createCollection(
                name, creator=creator, public=public)
        else:
            # If using a pre-existing collection, we must make sure we have
            # full access to it.
            self.model('collection').requireAccess(
                collection, user=creator, level=AccessType.ADMIN)

        challenge = {
            'name': name,
            'creatorId': creator['_id'],
            'collectionId': collection['_id'],
            'description': description,
            'instructions': instructions,
            'created': datetime.datetime.utcnow(),
            'organizers': organizers,
            'startDate': startDate,
            'endDate': endDate
        }

        self.setPublic(challenge, public=public)
        self.setUserAccess(challenge, user=creator, level=AccessType.ADMIN)

        return self.save(challenge)
