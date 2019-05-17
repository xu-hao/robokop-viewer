import React from 'react';
import ReactDOM from 'react-dom';
import { Provider } from 'mobx-react';

// Import static css, image, and font assets so that they can be found by webpack.
import 'bootstrap/dist/css/bootstrap.css'; // path search within node_modules
import 'ag-grid/dist/styles/ag-grid.css';
import 'ag-grid/dist/styles/ag-theme-material.css';
import 'react-select/dist/react-select.css';
import 'react-widgets/dist/css/react-widgets.css';

import 'babel-polyfill'; // For IE Promises

import SimpleViewer from './SimpleViewer';

// Our actual CSS and other images etc.
import '../assets/css/style.css';
import '../assets/images/favicon.ico';

const $ = require('jquery');

window.jQuery = window.$ = $; // eslint-disable-line

require('bootstrap');
const config = {
  ui: {
    enableNewAnswersets: true,
    enableNewQuestions: true,
    enableQuestionRefresh: true,
    enableQuestionEdit: true,
    enableQuestionDelete: true,
    enableQuestionFork: true,
    enableTaskStatus: true,
    enableAnswerFeedback: true,
  },
  // Add environmental dependent variables to config here.
  host: process.env.ROBOKOP_HOST,
  port: process.env.MANAGER_PORT,
  protocol: process.env.ROBOKOP_PROTOCOL,
};

const robokop = {
  config,
  simpleView: (id) => {
    ReactDOM.render(
      <SimpleViewer
        config={config}
        id={id}
      />,
      document.getElementById('reactEntry'),
    );
  }
};

export { robokop, config };

