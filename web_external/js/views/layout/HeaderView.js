covalic.views.LayoutHeaderView = covalic.View.extend({

    render: function () {
        this.$el.html(jade.templates.layoutHeader());


        // TODO this will probably have to be changed from folders and possibly my account
        new covalic.views.LayoutHeaderUserView({
            el: this.$('.g-current-user-wrapper')
        }).render();
    }

});
