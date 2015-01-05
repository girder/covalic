covalic.views.LeaderboardView = covalic.View.extend({
    initialize: function (settings) {
        this.phase = settings.phase;
        this.render();
    },

    render: function () {
        this.$el.html(covalic.templates.leaderboardPage({
            phase: this.phase
        }));

        new covalic.views.SubmissionListWidget({
            el: this.$('.c-leaderboard-container'),
            phase: this.phase,
            parentView: this
        });
    }
});

covalic.router.route('phase/:id/leaderboard', 'phase_leaderboard', function (id, params) {
    var phase = new covalic.models.PhaseModel();
    phase.set({
        _id: id
    }).on('g:fetched', function () {
        girder.events.trigger('g:navigateTo', covalic.views.LeaderboardView, {
            phase: phase
        });
    }, this).on('g:error', function () {
        covalic.router.navigate('challenges', {trigger: true});
    }, this).fetch();
});
