import { getCurrentUser } from 'girder/auth';
import { AccessType } from 'girder/constants';
import { cancelRestRequests } from 'girder/rest';
import PaginateWidget from 'girder/views/widgets/PaginateWidget';
import SearchFieldWidget from 'girder/views/widgets/SearchFieldWidget';

import router from '../../router';
import View from '../view';
import ChallengeCollection from '../../collections/ChallengeCollection';
import template from '../../templates/body/challengeList.pug';
import '../../stylesheets/body/challengeList.styl';

var ChallengesView = View.extend({
    events: {
        'change .c-challenges-filter': 'challengeFilterChanged'
    },

    initialize: function (settings) {
        cancelRestRequests('fetch');

        this.timeframe = settings.timeframe || 'all';

        var params = { timeframe: this.timeframe };

        this.collection = new ChallengeCollection();
        this.collection.on('g:changed', function () {
            this.render();
        }, this).fetch(params);

        this.paginateWidget = new PaginateWidget({
            collection: this.collection,
            parentView: this
        });

        this.searchWidget = new SearchFieldWidget({
            placeholder: 'Search challenges...',
            types: ['challenge.covalic'],
            getInfoCallback: function (type, obj) {
                if (type === 'challenge.covalic') {
                    return {
                        text: obj.name,
                        icon: 'flag-checkered'
                    };
                }
            },
            parentView: this
        }).on('g:resultClicked', this._gotoChallenge, this);
    },

    render: function () {
        var currentUser = getCurrentUser();
        this.$el.html(template({
            challenges: this.collection.toArray(),
            admin: !!(currentUser && currentUser.get('admin')),
            currentUser,
            AccessType,
            timeframe: this.timeframe
        }));

        this.paginateWidget.setElement(this.$('.c-challenge-pagination')).render();
        this.searchWidget.setElement(this.$('.c-challenges-search-container')).render();

        this.$('.c-tooltip').tooltip({
            delay: 100,
            container: this.$el,
            placement: function (tip, el) {
                return $(el).attr('placement') || 'top';
            }
        });

        return this;
    },

    _gotoChallenge: function (challenge) {
        router.navigate(`challenge/${challenge.id}`, {trigger: true});
    },

    challengeFilterChanged: function (e) {
        var select = e.currentTarget;
        this.timeframe = select.value;
        router.navigate(`challenges?timeframe=${this.timeframe}`, {
            replace: true
        });

        var params = { timeframe: this.timeframe };
        // FIXME fetch() ignores params when reset is true
        // Workaround: set params explicitly
        // this.collection.fetch(params, true);
        this.collection.params = params;
        this.collection.fetch(null, true);
    }
});

export default ChallengesView;
