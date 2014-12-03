covalic.App = Backbone.View.extend({
    el: 'body',

    initialize: function(settings) {
        girder.restRequest({
            path: 'user/me'
        }).done(_.bind(function (user) {
            girder.eventStream = new girder.EventStream();

            if (user) {
                girder.currentUser = new girder.models.UserModel(user);
                girder.eventStream.open();
            }
            this.render();

            // Once we've rendered the layout, we can start up the routing.
            Backbone.history.start({
                pushState: false
            });
        }, this));
    },

    render: function() {
        this.$el.html(jade.templates.layout());

        new covalic.views.LayoutHeaderView({
            el: this.$('#c-app-header-container')
        }).render();

        new covalic.views.ChallengesView({
            el: this.$('#c-app-body-container')
        }).render();


        return this;
    },
});
