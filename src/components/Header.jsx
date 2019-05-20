import React from 'react';

import { Navbar, Nav, NavItem, NavDropdown, MenuItem } from 'react-bootstrap';

import AppConfig from '../AppConfig';

class Header extends React.Component {
  constructor(props) {
    super(props);

    // We only read the communications config on instantiation
    this.appConfig = new AppConfig(props.config);
  }

  getPropsData() {
    return { status: this.props.status };
  }

  getNotLoggedInFrag() {
    return (
      <NavItem eventKey={4} href={this.appConfig.urls.login}>
        {'Log In'}
      </NavItem>
    );
  }

  render() {
    const data = this.getPropsData();

    const hasStatus = data.status && data.status.length > 0;
    const showApps = true;

    return (
      <Navbar
        style={{
          backgroundColor: this.appConfig.colors.bluegray,
          boxShadow: '0px 0px 5px 0px #b3b3b3',
          // backgroundImage: `linear-gradient(315deg, ${this.appConfig.colors.blue} 0%, ${this.appConfig.colors.bluegray} 74%)`,
        }}
        staticTop
      >
        <Navbar.Header>
          <Navbar.Brand>
            <a href="/simple/view">Robokop Viewer</a>
          </Navbar.Brand>
          <Navbar.Toggle />
        </Navbar.Header>
        <Navbar.Collapse>
          <Nav>
            {hasStatus &&
              <Navbar.Text>
                {data.status}
              </Navbar.Text>
            }
          </Nav>
          <Nav pullRight>
            {showApps &&
            <NavDropdown eventKey={3} title="Apps" id="basic-nav-dropdown">
              <MenuItem eventKey={3.2} href={this.appConfig.urls.view}>Answer Set Explorer - <small>Use the Robokop Viewer UI with answer set files.</small></MenuItem>
            </NavDropdown>
            }
          </Nav>
        </Navbar.Collapse>
      </Navbar>
    );
  }
}

Header.defaultProps = {
  status: '',
};

export default Header;
