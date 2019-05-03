import React from 'react';

import { DropdownList } from 'react-widgets';
import { Grid, Row, Col, Form, FormGroup, Button } from 'react-bootstrap';

import AppConfig from './AppConfig';
import AnswersetStore from './stores/messageAnswersetStore';
import Header from './components/Header';
import Footer from './components/Footer';
import Loading from './components/Loading';
import MessageAnswersetTable from './components/answerset/MessageAnswersetTable';
import CurieSelectorContainer from './components/shared/CurieSelectorContainer';
import entityNameDisplay from './components/util/entityNameDisplay';


class SimpleExpand extends React.Component {
  constructor(props) {
    super(props);
    // We only read the communications config on creation
    this.appConfig = new AppConfig(props.config);

    this.state = {
      user: {},
      concepts: [],
      type1: '',
      type2: '',
      identifier: '',
      term: '',
      resultsLoading: false,
      resultsReady: false,
      resultsFail: false,
    };

    this.initializeState = this.initializeState.bind(this);
    this.updateType = this.updateType.bind(this);
    this.onSearch = this.onSearch.bind(this);
    this.handleCurieChange = this.handleCurieChange.bind(this);
    this.getResults = this.getResults.bind(this);

    this.answersetStore = '';
  }

  componentDidMount() {
    this.initializeState();
  }

  initializeState() {
    // makes the appropriate GET request from server.py,
    // uses the result to set this.state
    this.appConfig.user(data => this.setState({
      user: this.appConfig.ensureUser(data),
      // userReady: true,
    }));
    this.appConfig.concepts(data => this.setState({
      concepts: data,
    }));
  }

  updateType(typeObj) {
    this.setState(typeObj);
  }

  onSearch(input, type) {
    return this.appConfig.questionNewSearch(input, type);
  }

  handleCurieChange(ty, te, cu) {
    if (cu || !te) {
      this.setState({ identifier: cu, term: te });
    }
  }

  getResults(event) {
    event.preventDefault();
    this.setState({ resultsLoading: true, resultsReady: false, resultsFail: false });
    const { type1, type2, identifier } = this.state;
    this.appConfig.simpleExpand(
      type1,
      type2,
      identifier,
      (data) => {
        this.answersetStore = new AnswersetStore(data);
        this.setState({
          resultsReady: true, resultsLoading: false,
        });
      },
      () => {
        this.setState({
          resultsFail: true, resultsLoading: false,
        });
      },
    );
  }

  render() {
    const { config } = this.props;
    const {
      user, concepts, type1, type2, identifier, resultsReady, resultsLoading, resultsFail, term,
    } = this.state;
    // if we don't have all the info, disable the submit.
    const disableSubmit = !(type1 && type2 && identifier) || resultsLoading;
    const types = concepts.map(concept => ({ text: entityNameDisplay(concept), value: concept }));
    return (
      <div>
        <Header config={config} user={user} />
        <Grid>
          <h1 style={{ textAlign: 'center' }}>Expanded Nodes</h1>
          <Form>
            <Row>
              <Col md={6}>
                <FormGroup controlId="node1">
                  <h3>
                    Node 1 Type
                  </h3>
                  <DropdownList
                    filter
                    data={types}
                    textField="text"
                    valueField="value"
                    value={type1}
                    onChange={value => this.updateType({ type1: value.value })}
                  />
                </FormGroup>
              </Col>
              <Col md={6}>
                <FormGroup controlId="node2">
                  <h3>
                    Node 2 Type
                  </h3>
                  <DropdownList
                    filter
                    data={types}
                    textField="text"
                    valueField="value"
                    value={type2}
                    onChange={value => this.updateType({ type2: value.value })}
                  />
                </FormGroup>
              </Col>
            </Row>
            <Row>
              <Col md={12}>
                {type1 &&
                  <div>
                    <h3>
                      Node 1 Curie
                    </h3>
                    <div
                      style={{
                          padding: '5px 0px',
                      }}
                    >
                      <CurieSelectorContainer
                        concepts={concepts}
                        search={this.onSearch}
                        disableType
                        initialInputs={{ type: type1, term, curie: identifier }}
                        onChangeHook={(ty, te, cu) => this.handleCurieChange(ty, te, cu)}
                      />
                    </div>
                  </div>
                }
              </Col>
            </Row>
            <Row style={{ textAlign: 'right', margin: '20px' }}>
              <Button id="submitAPI" onClick={this.getResults} disabled={disableSubmit}>Submit</Button>
            </Row>
          </Form>
          <Row style={{ margin: '20px 0px' }}>
            {resultsLoading &&
              <Loading />
            }
            {resultsReady &&
              <MessageAnswersetTable
                concepts={types}
                store={this.answersetStore}
                simpleExpand
                fileName={`${type1}(${identifier})_to_${type2}_expanded`}
              />
            }
            {resultsFail &&
              <h3>
                No results came back. Please try a different query.
              </h3>
            }
          </Row>
        </Grid>
        <Footer config={config} />
      </div>
    );
  }
}

export default SimpleExpand;