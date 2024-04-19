import {createApp} from 'mantra-core';
import {initContext} from './configs/context';

import core from './modules/core';

const context = initContext();

const app = createApp(context);
app.loadModule(core);
app.init();
