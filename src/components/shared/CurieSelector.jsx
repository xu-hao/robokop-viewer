import React from 'react';
import PropTypes from 'prop-types';
import { FormGroup, FormControl, InputGroup, Glyphicon } from 'react-bootstrap';
import { DropdownList } from 'react-widgets';

import BionamesBrowser from './BionamesBrowser';
import entityNameDisplay from '../util/entityNameDisplay';

const _ = require('lodash');

const propTypes = {
  term: PropTypes.string.isRequired,
  type: PropTypes.string.isRequired,
  curie: PropTypes.string.isRequired,
  concepts: PropTypes.arrayOf(PropTypes.string).isRequired,
  onClear: PropTypes.func.isRequired, // When X icon is clicked to clear input
  onReopen: PropTypes.func.isRequired, // When triangle drop-down icon is clicked
  onTypeChange: PropTypes.func.isRequired, // When type changed by drop-down selection
  onTermChange: PropTypes.func.isRequired, // When term input field is typed in
  onSelect: PropTypes.func.isRequired, // When entity is selected: (type, term, curie) => {}
  disableType: PropTypes.bool, // Whether to display the Type drop-down
  width: PropTypes.number,
  search: PropTypes.func,
  size: PropTypes.string, // undefined (default size) or 'small', 'xsmall', 'large'
};

const defaultProps = {
  search: () => Promise.resolve({ options: [] }),
  width: 0, // will be ignored
  disableType: true,
};

class CurieSelector extends React.Component {
  /*
  Note: All handlers (in props) must ensure that the supplied props.curie is
  always invalidated into an empty string any time the user takes an action
  that moves it away from a "selected" state.
  */
  constructor(props) {
    super(props);

    this.handleSearch = this.handleSearch.bind(this);
    this.wrapSearch = this.wrapSearch.bind(this);
    this.debouncedHandleSearch = _.debounce(this.handleSearch, 250);
    this.handleSelect = this.handleSelect.bind(this);
    this.handleTypeChange = this.handleTypeChange.bind(this);
    this.handleTermChange = this.handleTermChange.bind(this);
    this.handleReopen = this.handleReopen.bind(this);

    this.state = {
      options: null,
      loadingOptions: false,
    };

    this.input = null; // Input reference for focusing
  }

  componentDidUpdate(prevProps) {
    if ((this.props.term !== prevProps.term)) { // Re-do search if term changes
      this.setState({ loadingOptions: true }, () => this.debouncedHandleSearch(this.props.term, this.props.type));
    }
  }

  // onInputFocus() {
  //   this.setState({ showOptions: true }, () => { this.onUnSelect(); this.handleTermChange({ target: { value: this.state.term } }); });
  // }
  // onUnSelect() {
  //   this.setState({ selected: null, hasSelected: false }, () => this.props.onUnSelect());
  // }
  handleSelect(value) {
    const term = value.label;
    const curie = value.value;
    this.props.onSelect(this.props.type, term, curie);
  }
  handleSearch(input, nodeType) {
    this.wrapSearch(input, nodeType).catch(() => this.setState({ options: [] }))
      .then((data) => {
        if (data.options) {
          this.setState({ options: data.options, loadingOptions: false });
        }
      });
  }
  wrapSearch(input, nodeType) {
    if (!input || (input.length < 3)) {
      return Promise.resolve({ options: null });
    }
    return this.props.search(input, nodeType);
  }
  handleTermChange(event) {
    this.props.onTermChange(event);
  }
  handleTypeChange(type) {
    this.input.focus();
    this.setState({ options: [] }, () => this.props.onTypeChange(type));
    // this.setState({ type }, () => this.handleTermChange({ target: { value: this.state.term } }));
  }
  handleReopen() {
    this.props.onReopen();
    this.input.focus();
  }

  render() {
    const {
      concepts, size, curie, type, term, onClear, disableType,
    } = this.props;
    const dropDownObjList = concepts.map(c => ({ text: entityNameDisplay(c), value: c }));
    const showOptions = curie === '';

    const rightButtonCallback = showOptions ? onClear : this.handleReopen;
    const rightButtonContents = showOptions ? (<Glyphicon glyph="remove" />) : (<Glyphicon glyph="triangle-bottom" />);

    const width = this.props.width ? this.props.width : '100%';
    const browserWidth = this.props.width ? this.props.width - 10 : 0;
    return (
      <div
        id="bionames"
        className="curie-selector"
        style={{
          position: 'relative',
          display: 'inline-block',
          width,
          marginBottom: '50px',
        }}
      >
        <div>
          <FormGroup style={{ marginBottom: 0 }}>
            <InputGroup>
              <DropdownList
                filter
                // dropUp
                disabled={disableType}
                style={{ display: 'table-cell', verticalAlign: 'middle', width: '200px' }}
                data={dropDownObjList}
                textField="text"
                valueField="value"
                value={type}
                onChange={value => this.handleTypeChange(value.value)}
              />
              <FormControl
                type="text"
                className="curieSelectorInput"
                bsSize={size}
                disabled={!type}
                style={{ borderLeft: 0, borderRight: 0 }}
                placeholder="Start typing to search."
                value={term}
                inputRef={(ref) => {
                  this.input = ref;
                }}
                onChange={this.handleTermChange}
              />
              {!showOptions &&
                <InputGroup.Addon
                  style={{ background: '#fff' }}
                >
                  {curie}
                </InputGroup.Addon>
              }
              <InputGroup.Addon
                onClick={rightButtonCallback}
                style={{ background: '#fff', cursor: 'pointer' }}
              >
                {rightButtonContents}
              </InputGroup.Addon>
            </InputGroup>
          </FormGroup>
        </div>
        {showOptions &&
          <div
            style={{
              position: 'absolute',
              border: '1px solid #d4d4d4',
              borderTop: 'none',
              zIndex: 99,
              top: '100%',
              left: 0,
              right: 0,
              overflowY: 'none',
              backgroundColor: '#fff',
              borderBottom: '1px solid #d4d4d4',
              marginLeft: '5px',
              marginRight: '5px',
              borderBottomLeftRadius: '4px',
              borderBottomRightRadius: '4px',
            }}
          >
            <BionamesBrowser
              thinking={this.state.loadingOptions}
              data={this.state.options}
              type={this.props.type}
              onSelect={this.handleSelect}
              width={browserWidth}
            />
          </div>
        }
      </div>
    );
  }
}

CurieSelector.propTypes = propTypes;
CurieSelector.defaultProps = defaultProps;

export default CurieSelector;
