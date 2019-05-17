#!/usr/bin/env python

"""Start Flask web server."""

import os

from flask import render_template

from manager.setup import app

@app.route('/simple/view/')
def viewer_blank():
    """Answerset Browser with upload capablitiy."""
    return render_template('simpleView.html', upload_id='')

# Run Webserver
if __name__ == '__main__':

    # Get host and port from environmental variables
    server_host = '0.0.0.0'
    server_port = int(os.environ['MANAGER_PORT'])

    app.run(
        host=server_host,
        port=server_port,
        debug=False,
        use_reloader=True
    )
