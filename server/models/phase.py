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
import json
import six

from bson.objectid import ObjectId
from girder.constants import AccessType
from girder.models.model_base import AccessControlledModel, ValidationException
from girder.utility.progress import noProgress
from girder.plugins.covalic.utility import validateDate


class Phase(AccessControlledModel):
    def initialize(self):
        self.name = 'challenge_phase'
        ordinalCompoundIndex = ([('challengeId', 1), ('ordinal', 1)], {})
        self.ensureIndices(('challengeId', 'name', ordinalCompoundIndex))

        self.exposeFields(level=AccessType.READ, fields={
            '_id', 'name', 'public', 'description', 'created', 'updated',
            'active', 'challengeId', 'folderId', 'participantGroupId',
            'groundTruthFolderId', 'testDataFolderId', 'instructions',
            'ordinal', 'startDate', 'endDate', 'type', 'hideScores',
            'matchSubmissions', 'enableOrganization', 'enableOrganizationUrl',
            'enableDocumentationUrl', 'requireOrganization',
            'requireOrganizationUrl', 'requireDocumentationUrl', 'metrics',
            'meta'})
        self.exposeFields(level=AccessType.ADMIN, fields={'scoreTask'})

    def list(self, challenge, user=None, limit=50, offset=0, sort=None):
        """
        List phases for a challenge.
        """
        cursor = self.find(
            {'challengeId': challenge['_id']}, limit=0, sort=sort)

        for r in self.filterResultsByPermission(cursor=cursor, user=user,
                                                level=AccessType.READ,
                                                limit=limit, offset=offset):
            yield r

    def validate(self, doc):
        if not doc.get('name'):
            raise ValidationException('Phase name must not be empty.',
                                      field='name')

        if not isinstance(doc.get('challengeId'), ObjectId):
            raise ValidationException('Must have a challenge ID for the phase.',
                                      field='challengeId')

        if doc.get('startDate'):
            doc['startDate'] = validateDate(doc['startDate'], 'startDate')
        if doc.get('endDate'):
            doc['endDate'] = validateDate(doc['endDate'], 'endDate')

        # Check that dates are in a sensible order
        if doc.get('startDate') and doc.get('endDate'):
            if doc['startDate'] >= doc['endDate']:
                raise ValidationException('Invalid start and end dates.',
                                          field='startDate')

        # Ensure dockerArgs is a proper JSON list. If not, convert it to one.
        if doc.get('scoreTask', {}).get('dockerArgs'):
            args = doc['scoreTask']['dockerArgs']
            if isinstance(args, six.string_types):
                try:
                    doc['scoreTask']['dockerArgs'] = json.loads(args)
                except ValueError:
                    raise ValidationException(
                        'Docker arguments must be specified as a JSON list.')

            if not isinstance(doc['scoreTask']['dockerArgs'], list):
                raise ValidationException('Docker arguments must be a list.')

        return doc

    def subtreeCount(self, phase):
        """
        Returns the subtree count of this phase, which is the number of
        submissions, plus one record for the phase itself.
        """
        return self.model(
            'submission', 'covalic').getAllSubmissions(phase).count() + 1

    def remove(self, phase, progress=noProgress):
        """
        Remove this phase, which also removes all submissions to it.
        """
        subModel = self.model('submission', 'covalic')
        for sub in subModel.getAllSubmissions(phase):
            subModel.remove(sub)
            progress.update(increment=1,
                            message='Deleted submission %s' % sub['title'])

        super(Phase, self).remove(phase, progress=progress)
        progress.update(increment=1, message='Deleted phase %s' % phase['name'])

    def createPhase(self, name, challenge, creator, ordinal, description='',
                    instructions='', active=False, public=True,
                    participantGroup=None, groundTruthFolder=None,
                    testDataFolder=None, startDate=None, endDate=None,
                    type='', hideScores=False, matchSubmissions=True,
                    enableOrganization=False, enableOrganizationUrl=False,
                    enableDocumentationUrl=False, requireOrganization=False,
                    requireOrganizationUrl=False, requireDocumentationUrl=False,
                    meta=None):
        """
        Create a new phase for a challenge. Will create a top-level folder under
        the challenge's collection. Will also create a new group for the
        participants of this phase unless an existing group is passed as the
        participantGroup parameter.

        :param name: The name of this phase. Do not include the challenge name
            in the phase name as that will cause redundant names to be
            displayed.
        :type name: str
        :param challenge: The challenge to which this phase belongs.
        :type challenge: dict
        :param creator: The user creating this phase.
        :type creator: dict
        :param participantGroup: If you wish to use an existing group for the
            phase's participants, pass that document as this param. If set to
            None, will make a new group based on the challenge and phase name.
        :type participantGroup: dict or None
        :param active: Whether this phase is active (i.e. accepting
            submissions).
        :type active: bool
        :param description: A description for this phase.
        :type description: str
        :param instructions: Instructions to participants for this phase.
        :type instructions: str
        :param public: Whether this phase is publicly visible.
        :type public: bool
        :param groundTruthFolder: The folder containing ground truth data
            for this challenge phase. If set to None, will create one under this
            phase's folder.
        :param testDataFolder: The folder containing the testing dataset for
            this phase. If set to None, will create one under this phase's
            folder.
        :type ordinal: int
        :param ordinal: This specifies the position of the phase in the
            challenge. No check for duplicate value are done, the user is
            responsible to maintain the consistency.
        :param startDate: The start date of the phase.
        :type startDate: str or datetime
        :param endDate: The end date of the phase.
        :type endDate: str or datetime
        :param type: The type of this phase.
        :type type: str
        :param hideScores: If scores should be hidden from participants, set
           this to True.
        :type hideScores: bool
        :param matchSubmissions: Whether to require that submission filenames
            match ground truth filenames.
        :type matchSubmissions: bool
        :param enableOrganization: Enable submission Organization field.
        :type enableOrganization: bool
        :param enableOrganizationUrl: Enable submission Organization URL field.
        :type enableOrganizationUrl: bool
        :param enableDocumentationUrl: Enable submission Documentation URL field.
        :type enableDocumentationUrl: bool
        :param requireOrganization: Require submission Organization field.
        :type requireOrganization: bool
        :param requireOrganizationUrl: Require submission Organization URL field.
        :type requireOrganizationUrl: bool
        :param requireDocumentationUrl: Require submission Documentation URL field.
        :type requireDocumentationUrl: bool
        :param meta: dict
        :param meta: Additional metadata associated with a phase
        """
        collection = self.model('collection').load(challenge['collectionId'],
                                                   force=True)

        # We must validate the phase before we actually create anything.
        phase = {
            'name': name,
            'description': description,
            'instructions': instructions,
            'active': active,
            'challengeId': challenge['_id'],
            'created': datetime.datetime.utcnow(),
            'ordinal': ordinal,
            'creator': creator['_id'],
            'startDate': startDate,
            'endDate': endDate,
            'type': type,
            'hideScores': hideScores,
            'matchSubmissions': matchSubmissions,
            'enableOrganization': enableOrganization,
            'enableOrganizationUrl': enableOrganizationUrl,
            'enableDocumentationUrl': enableDocumentationUrl,
            'requireOrganization': requireOrganization,
            'requireOrganizationUrl': requireOrganizationUrl,
            'requireDocumentationUrl': requireDocumentationUrl,
            'meta': meta or {}
        }
        self.validate(phase)

        folder = self.model('folder').createFolder(
            collection, name, parentType='collection', public=public,
            creator=creator, allowRename=True)
        phase['folderId'] = folder['_id']

        if groundTruthFolder is None:
            groundTruthFolder = self.model('folder').createFolder(
                folder, 'Ground truth', parentType='folder', public=False,
                creator=creator, allowRename=True)
        phase['groundTruthFolderId'] = groundTruthFolder['_id']

        if testDataFolder is None:
            testDataFolder = self.model('folder').createFolder(
                folder, 'Test dataset', parentType='folder', public=False,
                creator=creator, allowRename=True)
        phase['testDataFolderId'] = testDataFolder['_id']

        if participantGroup is None:
            groupName = '%s %s participants' % (challenge['name'], name)
            participantGroup = self.model('group').findOne({'name': groupName})
            if participantGroup is None:
                participantGroup = self.model('group').createGroup(
                    groupName, creator, public=public)
        phase['participantGroupId'] = participantGroup['_id']

        self.setPublic(phase, public=public)
        self.setUserAccess(phase, user=creator, level=AccessType.ADMIN)
        self.setGroupAccess(phase, participantGroup, level=AccessType.READ)
        self.model('folder').setGroupAccess(testDataFolder, participantGroup,
                                            level=AccessType.READ, save=True)

        return self.save(phase)

    def updatePhase(self, phase):
        """
        Updates a phase.

        :param phase: The phase document to update
        :type phase: dict
        :returns: The phase document that was edited.
        """
        phase['updated'] = datetime.datetime.utcnow()

        # Validate and save the phase
        return self.save(phase)
