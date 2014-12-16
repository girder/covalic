/**
 * This widget shows a sorted list of submissions. It is used to render the
 * leaderboard but can be sorted in other ways as well.
 */
covalic.views.SubmissionListWidget = covalic.View.extend({
    events: {
        'click .c-score-link': function (e) {
            var id = $(e.currentTarget).attr('submission-id');
            covalic.router.navigate('submission/' + id, {trigger: true});
        }
    },

    initialize: function (settings) {
        this.phase = settings.phase;

        new girder.views.LoadingAnimation({
            el: this.$el
        }).render();

        this.collection = new covalic.collections.SubmissionCollection();
        this.collection.on('g:changed', function () {
            this.render();
        }, this).fetch({
            phaseId: this.phase.get('_id')
        });
    },

    render: function () {
        this.$el.html(covalic.templates.leaderboard({
            submissions: this.collection.models,
            offset: this.collection.offset,
            Math: Math
        }));

        new girder.views.PaginateWidget({
            el: this.$('.c-leaderboard-pagination'),
            collection: this.collection
        }).render();
    }
});
