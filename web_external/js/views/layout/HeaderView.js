covalic.views.LayoutHeaderView = covalic.View.extend({

    events: {
        'click .g-app-title': function(event) {
            covalic.router.navigate('/', {trigger: true});
        },
    },

    render: function () {
        this.$el.html(covalic.templates.layoutHeader());

        new covalic.views.LayoutHeaderUserView({
            el: this.$('.g-current-user-wrapper')
        }).render();
    }

});
