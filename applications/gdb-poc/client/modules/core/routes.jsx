import React from 'react';
import {FlowRouter} from 'meteor/kadira:flow-router';
import {mount} from 'react-mounter';

import MainLayout from './components/main_layout.jsx';
import GDB from '../gdb/gdb.jsx';

export default (injectDeps) => {
    const MainLayoutCtx = injectDeps(MainLayout);

    FlowRouter.route('/', {
        name: 'home',
        action() {
            mount(MainLayoutCtx, {
                content: (context) => ( <GDB {...context}/> );
            });
        }
    });
}
