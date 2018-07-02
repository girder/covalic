import _ from 'underscore';
import { getCurrentUser } from 'girder/auth';
import { AccessType } from 'girder/constants';
import { confirm } from 'girder/dialog';
import events from 'girder/events';
import { renderMarkdown } from 'girder/misc';
import { cancelRestRequests, restRequest } from 'girder/rest';
import FolderModel from 'girder/models/FolderModel';
import ItemModel from 'girder/models/ItemModel';

import router from '../../router';
import View from '../view';
import ChallengeModel from '../../models/ChallengeModel';
import EditPhaseWidget from '../widgets/EditPhaseWidget';
import EditScoringWidget from '../widgets/EditScoringWidget';
import LeaderboardWidget from '../widgets/LeaderboardWidget';
import template from '../../templates/body/phasePage.pug';
import '../../stylesheets/body/phasePage.styl';

var PhaseView = View.extend({
    events: {
        'click #c-join-phase': function () {
            if (!getCurrentUser()) {
                events.trigger('g:loginUi');
            } else {
                restRequest({
                    path: `challenge_phase/${this.model.id}/participant`,
                    type: 'POST',
                    error: null
                }).done(() => {
                    var participantGroupId = this.model.get('participantGroupId');
                    getCurrentUser().addToGroup(participantGroupId);
                    this.trigger('c:joinPhase');
                });
            }
        },

        'click a.c-edit-phase': function () {
            if (!this.editPhaseWidget) {
                this.editPhaseWidget = new EditPhaseWidget({
                    el: $('#g-dialog-container'),
                    model: this.model,
                    parentView: this
                }).on('g:saved', function () {
                    this.render();
                }, this);
            }
            this.editPhaseWidget.render();
        },

        'click .c-edit-scoring': function () {
            if (!this.editScoringWidget) {
                this.editScoringWidget = new EditScoringWidget({
                    el: $('#g-dialog-container'),
                    model: this.model,
                    parentView: this
                }).on('g:saved', function () {
                    this.render();
                }, this);
            }
            this.editScoringWidget.render();
        },

        'click .c-delete-phase': function () {
            confirm({
                text: 'Are you sure you want to delete the phase <b>' +
                      this.model.escape('name') + '</b>?',
                yesText: 'Delete',
                escapedHtml: true,
                confirmCallback: () => {
                    this.model.once('g:deleted', function () {
                        events.trigger('g:alert', {
                            icon: 'ok',
                            text: 'Phase deleted.',
                            type: 'success',
                            timeout: 4000
                        });
                        router.navigate(
                            'challenge/' + this.model.get('challengeId'), {
                                trigger: true
                            });
                    }, this).destroy({
                        progress: true
                    });
                }
            });
        }
    },

    initialize: function (settings) {
        this.on('c:joinPhase', function () {
            this.render();
            this._showDatasetDownloadButtons();
        }, this);

        cancelRestRequests('fetch');
        if (settings.phase) {
            this.model = settings.phase;

            this.challenge = new ChallengeModel({
                _id: this.model.get('challengeId')
            }).on('g:fetched', function () {
                this.render();
                this._showDatasetDownloadButtons();
            }, this);
            this.challenge.fetch();
        }
    },

    _showDatasetDownloadButtons: function () {
        if (this.model.get('groundTruthFolderId')) {
            var gtFolder = new FolderModel({
                _id: this.model.get('groundTruthFolderId')
            });
            gtFolder.once('g:fetched', function () {
                this.model.once('c:groundtruthItemsFetched', function (resp) {
                    var downloadUrl;
                    if (resp.length === 1) {
                        downloadUrl = new ItemModel({
                            _id: resp[0]._id
                        }).downloadUrl();
                    } else {
                        downloadUrl = gtFolder.downloadUrl();
                    }
                    this.$('.c-download-ground-truth').removeClass('hide')
                        .attr('href', downloadUrl);
                }, this).fetchGroundtruthItems();
            }, this).fetch({
                ignoreError: true
            });
        }

        if (this.model.get('testDataFolderId')) {
            var testFolder = new FolderModel({
                _id: this.model.get('testDataFolderId')
            });
            testFolder.once('g:fetched', function () {
                this.model.once('c:testDataItemsFetched', function (coll) {
                    var downloadUrl;
                    if (coll.models.length === 1) {
                        downloadUrl = coll.models[0].downloadUrl();
                    } else {
                        downloadUrl = testFolder.downloadUrl();
                    }
                    this.$('.c-download-test-data').removeClass('hide')
                        .attr('href', downloadUrl);
                }, this).fetchTestDataItems({limit: 2});
            }, this).fetch({
                ignoreError: true
            });
        }
    },

    isUserInChallenge: function () {
        if (!getCurrentUser()) {
            return false;
        }
        var participantGroupId = this.model.get('participantGroupId');
        var userGroupIds = getCurrentUser().get('groups');
        return _.contains(userGroupIds, participantGroupId);
    },

    render: function () {
        this.$el.html(template({
            phase: this.model,
            AccessType,
            userInChallenge: this.isUserInChallenge(),
            challenge: this.challenge
        }));

        renderMarkdown(this.model.get('instructions') || '*No overview provided.*',
            this.$('.c-phase-instructions-container'));

        if (!this.model.get('hideScores') ||
                this.model.getAccessLevel() >= AccessType.WRITE) {
            new LeaderboardWidget({
                phase: this.model,
                el: this.$('.c-leaderboard-widget-container'),
                parentView: this
            }).render();
        } else {
            this.$('.c-leaderboard-outer-wrapper').hide();
        }

        this.$('button[title]').tooltip({
            placement: 'left',
            container: this.$el
        });

        return this;
    }
});

export default PhaseView;
