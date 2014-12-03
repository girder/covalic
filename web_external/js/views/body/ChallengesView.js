covalic.views.ChallengesView = covalic.View.extend({

    initialize: function (settings) {
        girder.cancelRestRequests('fetch');
        this.collection = new girder.collections.ChallengeCollection();
        this.collection.on('g:changed', function () {
            this.render();
        }, this).fetch();
    },


    render: function() {
        console.log(this.collection.models);
        this.$el.html(jade.templates.challengeList({challenges: this.collection.models}));

        return this;
    }



});
