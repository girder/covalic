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
from girder.constants import AccessType, STATIC_ROOT_DIR
from girder.models.model_base import ValidationException
from girder.models.folder import Folder
from girder.models.user import User
from girder.plugin import getPlugin, GirderPlugin, loadedPlugins, registerPluginWebroot
from girder.utility import mail_utils
from girder.utility.model_importer import ModelImporter
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
              href="${staticRoot}/built/plugins/covalic_external/plugin.min.css">
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
        <script src="${staticRoot}/built/girder_app.min.js"></script>
        % for plugin in pluginJs:
          <script src="${staticRoot}/built/plugins/${plugin}/plugin.min.js"></script>
        % endfor
        <script src="${staticRoot}/built/plugins/covalic_external/plugin.min.js"></script>
      </body>
    </html>
    """

    def GET(self):
        if self.indexHtml is None:
            self.vars['pluginCss'] = []
            self.vars['pluginJs'] = []

            builtDir = os.path.join(
                STATIC_ROOT_DIR, 'built', 'plugins')
            plugins = loadedPlugins()

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
        User().load(
            event.info['value'], force=True, exc=True)
        event.preventDefault().stopPropagation()


def challengeSaved(event):
    """
    After a challenge is saved, we want to update the Assets folder permissions
    to be the same as the challenge.
    """
    challenge = event.info
    folder = getAssetsFolder(challenge, getCurrentUser(), False)
    Folder().copyAccessPolicies(
        challenge, folder, save=True)


def onPhaseSave(event):
    """
    Hook into phase save event to synchronize access control between the phase
    and submission folders for the phase.
    """
    phase = event.info
    submissions = Submission().getAllSubmissions(phase)
    Submission().updateFolderAccess(phase, submissions)


def onJobUpdate(event):
    """
    Hook into job update event so we can look for job failure events and email
    the user and challenge/phase administrators accordingly. Here, an
    administrator is defined to be a user with WRITE access or above.
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
        mail_utils.sendEmail(
            to=emails, subject='Submission processing error', text=html)

        # Mail user, include minimal log
        if not rescoring:
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

        registerPluginWebroot(CustomAppRoot(), 'covalic')

        events.bind('jobs.job.update', 'covalic', onJobUpdate)
        events.bind('model.setting.validate', 'covalic', validateSettings)
        events.bind('model.challenge_challenge.save.after', 'covalic',
                    challengeSaved)
        events.bind('model.challenge_phase.save.after', 'covalic',
                    onPhaseSave)
        events.bind('model.user.save.after', 'covalic', onUserSave)
