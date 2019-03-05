import events from '@girder/core/events';
import router from '@girder/core/router';
import { exposePluginConfig } from '@girder/core/utilities/PluginUtils';

exposePluginConfig('covalic', 'plugins/covalic/config');

import ConfigView from './views/ConfigView'; // eslint-disable-line import/first
router.route('plugins/covalic/config', 'covalicConfig', function () {
    events.trigger('g:navigateTo', ConfigView);
});
