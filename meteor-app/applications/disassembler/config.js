var disassemblerApp = {
    appID : '872009f8-adfb-4b6e-be1e-bda5ee845a7d',
    appName : 'Disassembler',
    package : 'Haevn',
    appOpen : true,
    layout : {
        windows : [
            {
                id : 'main',
                title : 'Haevn Disassembler',
                focused : true,
                top: '15px',
                left : '15px',
                height : '800px',
                width : '1000px',
                menubar : HAEVN_MENUBAR,
                pane_tree : {
                    id : 'main_pane',
                    panes : {
                        split_orientation : 'horizontal',
                        split_percent : '66%',
                        pane1 : {
                            id : 'main_pane1',
                            panes : {
                                split_orientation : 'vertical',
                                split_percent : '66%',
                                pane1 : {
                                    id : 'main_pane1.1'
                                },
                                pane2 : {
                                    id : 'main_pane1.2'
                                }
                            }
                        },
                        pane2 : {
                            id : 'main_pane2'
                        }
                    }
                }
            }
               
        ],

        tabs : [
            {
                id : 'disassembler-tab',
                title : 'Disassembler',
                pane_id : 'main_pane1.1',
                active : true,
                template : 'disassembler'
            },
            {
                id : 'console-tab',
                title : 'Console',
                pane_id : 'main_pane2',
                active : true,
                template : 'console'
            },
            {
                id : 'chat-tab',
                title : 'Chat',
                pane_id : 'main_pane2',
                active : false,
                template : 'chat'
            },
            {
                id : 'labels-tab',
                title : 'Labels',
                pane_id : 'main_pane1.2',
                active : true,
                template : 'labels'
            }
        ]
    }
};

MeteorOS.registerApp(disassemblerApp);
