covalic.views.PhaseView = covalic.View.extend({

    events: {
        'click #c-join-phase': function () {
            if (!girder.currentUser) {
                girder.events.trigger('g:loginUi');
            } else {
                var path = 'challenge_phase/' + this.model.get('_id') + '/participant';
                var type = 'POST';
                girder.restRequest({
                    path: path,
                    type: type,
                    error: null // TODO what?
                }).done(_.bind(function () {
                    var participantGroupId = this.model.get('participantGroupId');
                    girder.currentUser.addToGroup(participantGroupId);
                    this.trigger('c:joinPhase');
                }, this));
            }
        },

        'click a.c-edit-phase': function () {
            if (!this.editPhaseWidget) {
                this.editPhaseWidget = new covalic.views.EditPhaseWidget({
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
                this.editScoringWidget = new covalic.views.EditScoringWidget({
                    el: $('#g-dialog-container'),
                    model: this.model,
                    parentView: this
                }).on('g:saved', function () {
                    this.render();
                }, this);
            }
            this.editScoringWidget.render();
        },

        'click .c-phase-access-control': function () {
            if (!this.accessWidget) {
                this.accessWidget = new girder.views.AccessWidget({
                    el: $('#g-dialog-container'),
                    model: this.model,
                    modelType: 'phase',
                    hideRecurseOption: true,
                    parentView: this
                }).on('g:saved', function () {
                    this.render();
                }, this);
            } else {
                this.accessWidget.render();
            }
        },

        'click .c-delete-phase': function () {
            girder.confirm({
                text: 'Are you sure you want to delete the phase <b>' +
                      this.model.escape('name') + '</b>?',
                yesText: 'Delete',
                escapedHtml: true,
                confirmCallback: _.bind(function () {
                    this.model.destroy({
                        progress: true
                    }).on('g:deleted', function () {
                        girder.events.trigger('g:alert', {
                            icon: 'ok',
                            text: 'Phase deleted.',
                            type: 'success',
                            timeout: 4000
                        });
                        covalic.router.navigate(
                            'challenge/' + this.model.get('challengeId'), {
                                trigger: true
                            });
                    }, this);
                }, this)
            });
        }
    },

    initialize: function (settings) {
        this.on('c:joinPhase', function () {
            this.render();
            this._showDatasetDownloadButtons();
        }, this);

        girder.cancelRestRequests('fetch');
        if (settings.phase) {
            this.model = settings.phase;

            this.challenge = new covalic.models.ChallengeModel();
            this.challenge.set({
                _id: this.model.get('challengeId')
            }).on('g:fetched', function () {
                this.render();
                this._showDatasetDownloadButtons();
            }, this).fetch();
        }
    },

    _showDatasetDownloadButtons: function () {
        if (this.model.get('groundTruthFolderId')) {
            var gtFolder = new girder.models.FolderModel({
                _id: this.model.get('groundTruthFolderId')
            });
            gtFolder.once('g:fetched', function () {
                this.model.once('c:groundtruthItemsFetched', function (resp) {
                    var downloadUrl;
                    if (resp.length === 1) {
                        downloadUrl = new girder.models.ItemModel({
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
            var testFolder = new girder.models.FolderModel({
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
        if (!girder.currentUser) {
            return false;
        }
        var participantGroupId = this.model.get('participantGroupId');
        var userGroupIds = girder.currentUser.attributes.groups;
        return _.contains(userGroupIds, participantGroupId);
    },

    render: function () {
        this.$el.html(covalic.templates.phasePage({
            phase: this.model,
            girder: girder,
            userInChallenge: this.isUserInChallenge(),
            challenge: this.challenge
        }));

        girder.renderMarkdown(this.model.get('instructions') || '*No overview provided.*',
                              this.$('.c-phase-instructions-container'));

        if (!this.model.get('hideScores') ||
                this.model.getAccessLevel() >= girder.AccessType.WRITE) {
            new covalic.views.LeaderboardWidget({
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

covalic.router.route('phase/:id', 'phase', function (id) {
    // Fetch the phase by id, then render the view.
    var phase = new covalic.models.PhaseModel();
    phase.set({
        _id: id
    }).on('g:fetched', function () {
        girder.events.trigger('g:navigateTo', covalic.views.PhaseView, {
            phase: phase
        });
    }, this).on('g:error', function () {
        covalic.router.navigate('challenges', {trigger: true});
    }, this).fetch();
});
