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

import os
import posixpath

from girder import events
from girder.api.rest import getCurrentUser
from girder.api.v1 import resource
from girder.constants import AccessType, STATIC_ROOT_DIR
from girder.models.model_base import ValidationException
from girder.models.folder import Folder
from girder.models.user import User
from girder.plugin import getPlugin, GirderPlugin, loadedPlugins, registerPluginWebroot
from girder.utility import mail_utils
from girder.utility.model_importer import ModelImporter
from girder.utility.webroot import WebrootBase
from girder_jobs.constants import JobStatus
from girder_jobs.models.job import Job

from covalic.constants import PluginSettings, JOB_LOG_PREFIX
from covalic.models.challenge import Challenge
from covalic.models.phase import Phase
from covalic.models.submission import Submission
from covalic.rest.challenge import ChallengeResource
from covalic.rest.phase import PhaseResource
from covalic.rest.submission import SubmissionResource
from covalic.utility import getAssetsFolder
from covalic.utility.user_emails import getPhaseUserEmails

_HERE = os.path.abspath(os.path.dirname(__file__))


def validateSettings(event):
    if event.info['key'] == PluginSettings.SCORING_USER_ID:
        if not event.info['value']:
            raise ValidationException(
                'Scoring user ID must not be empty.', 'value')
        User().load(
            event.info['value'], force=True, exc=True)
        event.preventDefault().stopPropagation()


def challengeSaved(event):
    """
    Event handler for challenge save.

    After a challenge is saved, we want to update the Assets folder permissions
    to be the same as the challenge.
    """
    challenge = event.info
    folder = getAssetsFolder(challenge, getCurrentUser(), False)
    Folder().copyAccessPolicies(
        challenge, folder, save=True)


def onPhaseSave(event):
    """
    Event handler for phase save.

    Hook into phase save event to synchronize access control between the phase
    and submission folders for the phase.
    """
    phase = event.info
    submissions = Submission().getAllSubmissions(phase)
    Submission().updateFolderAccess(phase, submissions)


def onJobUpdate(event):
    """
    Look for job failure events and email the user and challenge/phase administrators accordingly.

    Here, an administrator is defined to be a user with WRITE access or above.
    """
    isErrorStatus = False
    try:
        isErrorStatus = int(event.info['params'].get('status')) == JobStatus.ERROR
    except (ValueError, TypeError):
        pass

    if (event.info['job']['type'] == 'covalic_score' and isErrorStatus):
        covalicHost = posixpath.dirname(mail_utils.getEmailUrlPrefix())

        # Create minimal log that contains only Covalic errors.
        # Use full log if no Covalic-specific errors are found.
        # Fetch log from model, because log in event may not be up-to-date.
        job = Job().load(
            event.info['job']['_id'], includeLog=True, force=True)
        log = job.get('log')

        minimalLog = None
        if log:
            log = ''.join(log)
            minimalLog = '\n'.join([line[len(JOB_LOG_PREFIX):].strip()
                                    for line in log.splitlines()
                                    if line.startswith(JOB_LOG_PREFIX)])
        if not minimalLog:
            minimalLog = log

        submission = Submission().load(
            event.info['job']['covalicSubmissionId'])
        phase = Phase().load(
            submission['phaseId'], force=True)
        challenge = Challenge().load(
            phase['challengeId'], force=True)
        user = User().load(
            event.info['job']['userId'], force=True)

        rescoring = job.get('rescoring', False)

        # Mail admins, include full log
        emails = sorted(getPhaseUserEmails(
            phase, AccessType.WRITE, includeChallengeUsers=True))
        html = mail_utils.renderTemplate('covalic.submissionErrorAdmin.mako', {
            'submission': submission,
            'challenge': challenge,
            'phase': phase,
            'user': user,
            'host': covalicHost,
            'log': log
        })
        mail_utils.sendMail('Submission processing error', html, emails)

        # Mail user, include minimal log
        if not rescoring:
            html = mail_utils.renderTemplate('covalic.submissionErrorUser.mako', {
                'submission': submission,
                'challenge': challenge,
                'phase': phase,
                'host': covalicHost,
                'log': minimalLog
            })
            mail_utils.sendMail('Submission processing error', html, [user['email']])


def onUserSave(event):
    """Update the user's name in their submissions, on user save."""
    user = event.info
    userName = Submission().getUserName(user)

    query = {
        'creatorId': user['_id']
    }
    update = {
        '$set': {
            'creatorName': userName
        }
    }
    Submission().update(query, update)


class CovalicPlugin(GirderPlugin):
    DISPLAY_NAME = 'COVALIC Challenges'

    def npmPackages(self):
        return {
            '@girder/covalic': 'file:%s/web_client' % _HERE,
            '@girder/covalic-external': 'file:%s/web_external' % _HERE
        }

    def load(self, info):
        getPlugin('gravatar').load(info)
        getPlugin('jobs').load(info)
        getPlugin('worker').load(info)
        getPlugin('thumbnails').load(info)

        mail_utils.addTemplateDirectory(os.path.join(_HERE, 'mail_templates'))
        ModelImporter.registerModel('challenge', Challenge, 'covalic')
        ModelImporter.registerModel('phase', Phase, 'covalic')
        ModelImporter.registerModel('submission', Submission, 'covalic')

        resource.allowedSearchTypes.add('challenge.covalic')

        info['apiRoot'].challenge = ChallengeResource()
        info['apiRoot'].challenge_phase = PhaseResource()
        info['apiRoot'].covalic_submission = SubmissionResource()

        webroot = WebrootBase(os.path.join(_HERE, 'webroot.mako'))
        webroot.updateHtmlVars({
            'pluginCss': [
                plugin for plugin in loadedPlugins()
                if os.path.exists(os.path.join(
                    STATIC_ROOT_DIR, 'built', 'plugins', plugin, 'plugin.min.css'))
            ],
            'pluginJs': [
                plugin for plugin in loadedPlugins()
                if os.path.exists(os.path.join(
                    STATIC_ROOT_DIR, 'built', 'plugins', plugin, 'plugin.min.js'))
            ]
        })
        registerPluginWebroot(webroot, 'covalic')

        events.bind('jobs.job.update', 'covalic', onJobUpdate)
        events.bind('model.setting.validate', 'covalic', validateSettings)
        events.bind('model.challenge_challenge.save.after', 'covalic',
                    challengeSaved)
        events.bind('model.challenge_phase.save.after', 'covalic',
                    onPhaseSave)
        events.bind('model.user.save.after', 'covalic', onUserSave)
