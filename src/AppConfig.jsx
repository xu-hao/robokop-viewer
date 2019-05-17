import axios from 'axios';
import axiosRetry from 'axios-retry';

class AppConfig {
  constructor(config) {
    this.config = config;

    this.comms = axios.create();
    this.questionNewSearchCancelToken = null; // Store cancelToken for get requests here (see https://github.com/axios/axios/issues/1361#issuecomment-366807250)
    axiosRetry(this.comms, { retries: 3 }); // Retry for request timeouts, help with spotty connections.
    this.cancelToken = axios.CancelToken.source();

    // Valid urls we would go to
    this.urls = {
      view: this.url('simple/view/'),
    };

    // Other URLs that are primarily used for API calls
    this.apis = {
      viewData: id => this.url(`api/simple/view/${id}`),
    };

    this.url = this.url.bind(this);

    this.viewData = this.viewData.bind(this);

    this.colors = {
      bluegray: '#f5f7fa',
      blue: '#b8c6db',
    };
  }

  url(ext) {
    return `${this.config.protocol}://${this.config.host}:${this.config.port}/${ext}`;
  }

  viewData(uploadId, successFun, failureFun) {
    this.getRequest(
      this.apis.viewData(uploadId),
      successFun,
      failureFun,
    );
  }

  open(url) {
    window.open(url, '_blank'); // This will not open a new tab in all browsers, but will try
  }
  redirect(newUrl) {
    window.location.href = newUrl;
  }
  back() {
    window.history.back();
  }
  replaceUrl(title, url) {
    window.history.replaceState({}, title, url);
  }

  getRequest(
    addr,
    successFunction = () => {},
    failureFunction = (err) => {
      window.alert('There was a problem contacting the server.');
      console.log('Problem with get request:');
      console.log(err);
      console.log(addr);
    },
  ) {
    this.comms.get(addr, { cancelToken: this.cancelToken.token }).then((result) => {
      successFunction(result.data); // 'ok'
    }).catch((err) => {
      failureFunction(err);
    });
  }

  postRequest(
    addr,
    data,
    successFunction = () => {},
    failureFunction = (err) => {
      window.alert('There was a problem contacting the server.');
      console.log('Problem with post request:');
      console.log(err);
    },
  ) {
    this.comms.post(addr, data).then((result) => {
      successFunction(result.data);
    }).catch((err) => {
      failureFunction(err);
    });
  }

  deleteRequest(
    addr,
    successFunction = () => {},
    failureFunction = (err) => {
      window.alert('There was a problem contacting the server.');
      console.log('Problem with delete request:');
      console.log(err);
    },
  ) {
    this.comms.delete(addr).then((result) => {
      successFunction(result);
    }).catch((err) => {
      failureFunction(err);
    });
  }

}

export default AppConfig;

