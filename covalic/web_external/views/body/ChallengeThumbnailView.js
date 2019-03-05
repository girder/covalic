import _ from 'underscore';

import router from '../../router';
import EditThumbnailWidget from '../widgets/EditThumbnailWidget';
import View from '../view';
import template from '../../templates/body/challengeThumbnailPage.pug';
import '../../stylesheets/widgets/wizards.styl';
import '../../stylesheets/body/challengeThumbnail.styl';

var ChallengeThumbnailView = View.extend({
    events: {
        'click .c-wizard-next-button': function () {
            router.navigate('challenge/' + this.model.id, {trigger: true});
        }
    },

    initialize: function (settings) {
        this.wizard = settings.wizard || false;
        if (this.wizard && !_.has(this.wizard, 'current')) {
            this.wizard.current = 0;
        }

        this.editThumbnailWidget = new EditThumbnailWidget({
            parentView: this,
            model: this.model
        });

        this.render();
    },

    render: function () {
        this.$el.html(template({
            challenge: this.model,
            wizard: this.wizard
        }));

        this.editThumbnailWidget.setElement(this.$('.c-thumbnail-widget-container')).render();

        return this;
    }
});

export default ChallengeThumbnailView;
