/**
* View for submissions to a phase.
*/
covalic.views.PhaseSubmissionsView = covalic.View.extend({
    initialize: function (settings) {
        girder.cancelRestRequests('fetch');

        var participantLimit = 5;
        if (!_.isNull(settings.participantLimit)) {
            participantLimit = Math.max(1, parseInt(settings.participantLimit, 10));
        }

        this.views = [];

        if (settings.phase) {
            this.phase = settings.phase;

            this.participants = new girder.collections.UserCollection();
            this.participants.altUrl =
                'group/' + this.phase.get('participantGroupId') + '/member';
            this.participants.pageLimit = participantLimit;
            this.participants.on('g:changed', function () {
                this.views = [];
                this.participants.each(_.bind(function (user) {
                    this.views.push(new covalic.views.UserSubmissionsView({
                        phase: this.phase,
                        user: user,
                        submissionLimit: settings.submissionLimit,
                        parentView: this
                    }));
                }, this));
                this.render();
            }, this).fetch();

            this.paginateWidget = new girder.views.PaginateWidget({
                collection: this.participants,
                parentView: this
            });
        }
    },

    render: function () {
        this.$el.html(covalic.templates.phaseSubmissionsPage({
            phase: this.phase
        }));

        var container = $('.c-user-submissions-container');

        _.each(this.views, function (view) {
            container.append(view.render().el);
        });

        this.paginateWidget.setElement(this.$('.c-phase-participants-pagination')).render();

        return this;
    }
});

covalic.router.route('phase/:id/submissions', 'phaseSubmissions', function (id, params) {
    var phase = new covalic.models.PhaseModel({
        _id: id
    }).once('g:fetched', function () {
        if (phase.getAccessLevel() < girder.AccessType.WRITE) {
            covalic.router.navigate('challenges', {trigger: true});
        } else {
            params = girder.parseQueryString(params);

            var participantLimit = null;
            var submissionLimit = null;
            if (_.has(params, 'participantLimit')) {
                participantLimit = params.participantLimit;
            }
            if (_.has(params, 'submissionLimit')) {
                submissionLimit = params.submissionLimit;
            }

            girder.events.trigger('g:navigateTo', covalic.views.PhaseSubmissionsView, {
                phase: phase,
                participantLimit: participantLimit,
                submissionLimit: submissionLimit
            });
        }
    }, this).on('g:error', function () {
        covalic.router.navigate('challenges', {trigger: true});
    }, this).fetch();
});
