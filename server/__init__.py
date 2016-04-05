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

import json
import mako
import os
import posixpath
import six

from girder import events
from girder.api.rest import getCurrentUser
from girder.constants import AccessType, SettingKey, STATIC_ROOT_DIR
from girder.models.model_base import ValidationException
from girder.plugins.jobs.constants import JobStatus
from girder.utility import mail_utils
from girder.utility.model_importer import ModelImporter
from .rest import challenge, submission, phase
from .constants import PluginSettings, JOB_LOG_PREFIX
from .utility import getAssetsFolder
from .utility.user_emails import getPhaseUserEmails


def validateSettings(event):
    if event.info['key'] == PluginSettings.SCORING_USER_ID:
        if not event.info['value']:
            raise ValidationException(
                'Scoring user ID must not be empty.', 'value')
        ModelImporter.model('user').load(
            event.info['value'], force=True, exc=True)
        event.preventDefault().stopPropagation()


def validatePhase(event):
    phase = event.info

    # Ensure dockerArgs is a proper JSON list. If not, convert it to one.
    if phase.get('scoreTask', {}).get('dockerArgs'):
        args = phase['scoreTask']['dockerArgs']
        if isinstance(args, six.string_types):
            try:
                phase['scoreTask']['dockerArgs'] = json.loads(args)
            except ValueError:
                raise ValidationException(
                    'Docker arguments must be specified as a JSON list.')

        if not isinstance(phase['scoreTask']['dockerArgs'], list):
            raise ValidationException('Docker arguments must be a list.')


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
        <link rel="stylesheet" href="${staticRoot}/built/girder.ext.min.css">
        <link rel="stylesheet" href="${staticRoot}/built/girder.app.min.css">
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
        <script src="${staticRoot}/built/girder.ext.min.js"></script>
        <script src="${staticRoot}/built/girder.app.min.js"></script>
        % for plugin in pluginJs:
          <script src="${staticRoot}/built/plugins/${plugin}/plugin.min.js">
          </script>
        % endfor
        <script src="${staticRoot}/built/plugins/covalic/covalic.min.js">
        </script>
        <script src="${staticRoot}/built/plugins/covalic/main.min.js"></script>
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


def deleteSubmissions(event):
    """
    Hook into deletion of a challenge phase and delete all corresponding
    submissions.
    """
    phase = event.info['document']
    subModel = ModelImporter.model('submission', 'covalic')

    submissions = subModel.find({
        'phaseId': phase['_id']
    }, limit=0)

    for sub in submissions:
        subModel.remove(sub)


def challengeSaved(event):
    """
    After a challenge is saved, we want to update the Assets folder permissions
    to be the same as the challenge.
    """
    challenge = event.info
    folder = getAssetsFolder(challenge, getCurrentUser(), False)
    ModelImporter.model('folder').copyAccessPolicies(
        challenge, folder, save=True)


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
        phase = ModelImporter.model('phase', 'challenge').load(
            submission['phaseId'], force=True)
        challenge = ModelImporter.model('challenge', 'challenge').load(
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


def load(info):
    # Extend challenge_phase resource
    info['apiRoot'].challenge = challenge.ChallengeExt()
    info['apiRoot'].challenge_phase = phase.PhaseExt()
    info['apiRoot'].covalic_submission = submission.Submission()

    # Move girder app to /girder, serve covalic app from /
    info['serverRoot'], info['serverRoot'].girder = (CustomAppRoot(),
                                                     info['serverRoot'])
    info['serverRoot'].api = info['serverRoot'].girder.api

    events.bind('model.challenge_phase.remove_with_kwargs', 'covalic',
                deleteSubmissions)
    events.bind('jobs.job.update', 'covalic', onJobUpdate)
    events.bind('model.setting.validate', 'covalic', validateSettings)
    events.bind('model.challenge_phase.validate', 'covalic', validatePhase)
    events.bind('model.challenge_challenge.save.after', 'covalic',
                challengeSaved)

    # Expose extended fields on models
    ModelImporter.model('phase', 'challenge').exposeFields(
        level=AccessType.READ, fields='metrics')
    ModelImporter.model('phase', 'challenge').exposeFields(
        level=AccessType.ADMIN, fields='scoreTask')
    ModelImporter.model('challenge', 'challenge').exposeFields(
        level=AccessType.READ, fields=('thumbnails', 'thumbnailSourceId'))
