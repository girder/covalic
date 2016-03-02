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
from girder.constants import AccessType, SettingKey, STATIC_ROOT_DIR
from girder.models.model_base import ValidationException
from girder.plugins.jobs.constants import JobStatus
from girder.utility import mail_utils
from girder.utility.model_importer import ModelImporter
from .rest import challenge, submission, phase
from .constants import PluginSettings


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


def onJobUpdate(event):
    """
    Hook into job update event so we can look for job failure events and email
    administrators accordingly.
    """
    if (event.info['job']['type'] == 'covalic_score' and
            'status' in event.info['params'] and
            int(event.info['params']['status']) == JobStatus.ERROR):
        covalicHost = posixpath.dirname(mail_utils.getEmailUrlPrefix())
        html = mail_utils.renderTemplate('covalic.submissionError.mako', {
            'submissionId': event.info['job']['covalicSubmissionId'],
            'host': covalicHost
        })
        mail_utils.sendEmail(
            toAdmins=True, subject='Submission processing error', text=html)


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

    # Expose extended fields on models
    ModelImporter.model('phase', 'challenge').exposeFields(
        level=AccessType.READ, fields='metrics')
    ModelImporter.model('phase', 'challenge').exposeFields(
        level=AccessType.SITE_ADMIN, fields='scoreTask')
    ModelImporter.model('challenge', 'challenge').exposeFields(
        level=AccessType.READ, fields=('thumbnails', 'thumbnailSourceId'))
