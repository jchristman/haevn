import React from 'react';

const MainLayout = (context) => {
    <div style={{ position: 'absolute', width: '100%', height: '100%' }}>
        { props.content(context) }
    </div>
}

export default MainLayout;
