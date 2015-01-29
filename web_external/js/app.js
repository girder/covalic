covalic.App = girder.App.extend({

    render: function() {
        this.$el.html(covalic.templates.layout());

        new covalic.views.LayoutHeaderView({
            el: this.$('#c-app-header-container'),
            parentView: this
        }).render();

        return this;
    },

});
