console.log("covalic app.js");
covalic.App = girder.App.extend({

    render: function() {
        this.$el.html(jade.templates.layout());

        new covalic.views.LayoutHeaderView({
            el: this.$('#g-app-header-container')
        }).render();

        new covalic.views.ChallengesView({
            el: this.$('#g-app-body-container')
        }).render();

        this.globalNavView = new covalic.views.LayoutGlobalNavView({
            el: this.$('#g-global-nav-container')
        }).render();

        return this;
    },

});

