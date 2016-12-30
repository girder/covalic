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

import mako
import os
import posixpath

from girder import events
from girder.api.rest import getCurrentUser
from girder.api.v1 import resource
from girder.constants import AccessType, SettingKey, STATIC_ROOT_DIR
from girder.models.model_base import ValidationException
from girder.plugins.jobs.constants import JobStatus
from girder.utility import mail_utils
from girder.utility.model_importer import ModelImporter
from girder.utility.plugin_utilities import registerPluginWebroot
from .rest import challenge, phase, submission
from .constants import PluginSettings, JOB_LOG_PREFIX
from .utility import getAssetsFolder
from .utility.user_emails import getPhaseUserEmails


class CustomAppRoot(ModelImporter):
    """
    The webroot endpoint simply serves the main index HTML file of covalic.
    """
    exposed = True

    indexHtml = None

    vars = {
        'apiRoot': '/api/v1',
        'staticRoot': '/static',
        'title': 'Covalic'
    }

    template = r"""
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>${title}</title>
        <link rel="stylesheet"
              href="//fonts.googleapis.com/css?family=Droid+Sans:400,700">
        <link rel="stylesheet"
              href="${staticRoot}/built/fontello/css/fontello.css">
        <link rel="stylesheet"
              href="${staticRoot}/built/fontello/css/animation.css">
        <link rel="stylesheet" href="${staticRoot}/built/girder_lib.min.css">
        <link rel="stylesheet"
              href="${staticRoot}/built/plugins/covalic/covalic.min.css">
        % for plugin in pluginCss:
            <link rel="stylesheet"
                  href="${staticRoot}/built/plugins/${plugin}/plugin.min.css">
        % endfor
        <link rel="icon"
              type="image/png"
              href="${staticRoot}/img/Girder_Favicon.png">

      </head>
      <body>
        <div id="g-global-info-apiroot" class="hide">${apiRoot}</div>
        <div id="g-global-info-staticroot" class="hide">${staticRoot}</div>
        <script src="${staticRoot}/built/girder_lib.min.js"></script>
        % for plugin in pluginJs:
          <script src="${staticRoot}/built/plugins/${plugin}/plugin.min.js"></script>
        % endfor
        <script src="${staticRoot}/built/plugins/covalic/covalic.min.js"></script>
      </body>
    </html>
    """

    def GET(self):
        if self.indexHtml is None:
            self.vars['pluginCss'] = []
            self.vars['pluginJs'] = []

            builtDir = os.path.join(
                STATIC_ROOT_DIR, 'clients', 'web', 'static', 'built', 'plugins')
            plugins = self.model('setting').get(SettingKey.PLUGINS_ENABLED, ())

            for plugin in plugins:
                if os.path.exists(os.path.join(builtDir, plugin,
                                               'plugin.min.css')):
                    self.vars['pluginCss'].append(plugin)
                if os.path.exists(os.path.join(builtDir, plugin,
                                               'plugin.min.js')):
                    self.vars['pluginJs'].append(plugin)
            self.indexHtml = mako.template.Template(self.template).render(
                **self.vars)

        return self.indexHtml


def validateSettings(event):
    if event.info['key'] == PluginSettings.SCORING_USER_ID:
        if not event.info['value']:
            raise ValidationException(
                'Scoring user ID must not be empty.', 'value')
        ModelImporter.model('user').load(
            event.info['value'], force=True, exc=True)
        event.preventDefault().stopPropagation()


def challengeSaved(event):
    """
    After a challenge is saved, we want to update the Assets folder permissions
    to be the same as the challenge.
    """
    challenge = event.info
    folder = getAssetsFolder(challenge, getCurrentUser(), False)
    ModelImporter.model('folder').copyAccessPolicies(
        challenge, folder, save=True)


def onPhaseSave(event):
    """
    Hook into phase save event to synchronize access control between the phase
    and submission folders for the phase.
    """
    phase = event.info
    submissionModel = ModelImporter.model('submission', 'covalic')
    submissions = submissionModel.getAllSubmissions(phase)
    submissionModel.updateFolderAccess(phase, submissions)


def onJobUpdate(event):
    """
    Hook into job update event so we can look for job failure events and email
    the user and challenge/phase administrators accordingly. Here, an
    administrator is defined to be a user with WRITE access or above.
    """
    if (event.info['job']['type'] == 'covalic_score' and
            'status' in event.info['params'] and
            int(event.info['params']['status']) == JobStatus.ERROR):
        covalicHost = posixpath.dirname(mail_utils.getEmailUrlPrefix())

        # Create minimal log that contains only Covalic errors.
        # Use full log if no Covalic-specific errors are found.
        log = event.info['job'].get('log')
        minimalLog = None
        if log:
            minimalLog = '\n'.join([line[len(JOB_LOG_PREFIX):].strip()
                                    for line in log.splitlines()
                                    if line.startswith(JOB_LOG_PREFIX)])
        if not minimalLog:
            minimalLog = log

        submission = ModelImporter.model('submission', 'covalic').load(
            event.info['job']['covalicSubmissionId'])
        phase = ModelImporter.model('phase', 'covalic').load(
            submission['phaseId'], force=True)
        challenge = ModelImporter.model('challenge', 'covalic').load(
            phase['challengeId'], force=True)
        user = ModelImporter.model('user').load(
            event.info['job']['userId'], force=True)

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
        mail_utils.sendEmail(
            to=emails, subject='Submission processing error', text=html)

        # Mail user, include minimal log
        html = mail_utils.renderTemplate('covalic.submissionErrorUser.mako', {
            'submission': submission,
            'challenge': challenge,
            'phase': phase,
            'host': covalicHost,
            'log': minimalLog
        })
        mail_utils.sendEmail(
            to=user['email'], subject='Submission processing error', text=html)


def onUserSave(event):
    """
    Hook into user save event and update the user's name in their submissions.
    """
    user = event.info
    subModel = ModelImporter.model('submission', 'covalic')
    userName = subModel.getUserName(user)

    query = {
        'creatorId': user['_id']
    }
    update = {
        '$set': {
            'creatorName': userName
        }
    }
    subModel.update(query, update)


def load(info):
    resource.allowedSearchTypes.add('challenge.covalic')

    info['apiRoot'].challenge = challenge.Challenge()
    info['apiRoot'].challenge_phase = phase.Phase()
    info['apiRoot'].covalic_submission = submission.Submission()

    registerPluginWebroot(CustomAppRoot(), info['name'])

    events.bind('jobs.job.update', 'covalic', onJobUpdate)
    events.bind('model.setting.validate', 'covalic', validateSettings)
    events.bind('model.challenge_challenge.save.after', 'covalic',
                challengeSaved)
    events.bind('model.challenge_phase.save.after', 'covalic',
                onPhaseSave)
    events.bind('model.user.save.after', 'covalic', onUserSave)
