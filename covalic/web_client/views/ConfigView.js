import _ from 'underscore';
import View from 'girder/views/View';
import SearchFieldWidget from 'girder/views/widgets/SearchFieldWidget';
import PluginConfigBreadcrumbWidget from 'girder/views/widgets/PluginConfigBreadcrumbWidget';
import { restRequest } from 'girder/rest';
import events from 'girder/events';

import template from '../templates/config.pug';
import '../stylesheets/config.styl';

/**
 * Administrative configuration view.
 */
const ConfigView = View.extend({
    events: {
        'submit #g-covalic-config-form': function (event) {
            event.preventDefault();
            this.$('#g-covalic-error-message').empty();

            this._saveSettings([{
                key: 'covalic.scoring_user_id',
                value: this.$('#g-scoring-user-id').val().trim()
            }]);
        }
    },

    initialize: function () {
        restRequest({
            type: 'GET',
            path: 'system/setting',
            data: {
                list: JSON.stringify([
                    'covalic.scoring_user_id'
                ])
            }
        }).done(_.bind(function (resp) {
            this.render();
            this.$('#g-scoring-user-id').val(resp['covalic.scoring_user_id']);
        }, this));

        this.searchWidget = new SearchFieldWidget({
            placeholder: 'Search for scoring user...',
            types: ['user'],
            parentView: this
        }).on('g:resultClicked', this._setCeleryUser, this);

        this.breadcrumb = new PluginConfigBreadcrumbWidget({
            pluginName: 'COVALIC challenges',
            parentView: this
        });
    },

    render: function () {
        this.$el.html(template());

        this.searchWidget.setElement(this.$('.g-scoring-user-select-container')).render();
        this.breadcrumb.setElement(this.$('.g-config-breadcrumb-container')).render();

        return this;
    },

    _setCeleryUser: function (user) {
        this.searchWidget.resetState();
        this.$('#g-scoring-user-id').val(user.id);
    },

    _saveSettings: function (settings) {
        restRequest({
            type: 'PUT',
            path: 'system/setting',
            data: {
                list: JSON.stringify(settings)
            },
            error: null
        }).done(_.bind(function () {
            events.trigger('g:alert', {
                icon: 'ok',
                text: 'Settings saved.',
                type: 'success',
                timeout: 4000
            });
        }, this)).error(_.bind(function (resp) {
            this.$('#g-covalic-error-message').text(
                resp.responseJSON.message);
        }, this));
    }
});

export default ConfigView;
