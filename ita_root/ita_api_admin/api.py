#   Copyright 2022 NEC Corporation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import os
import connexion

from dotenv import load_dotenv  # python-dotenv
from libs.admin_common import before_request_handler
# import secrets
# import string


# load environ variables
load_dotenv(override=True)

flask_app = connexion.FlaskApp(__name__, specification_dir='./swagger/')
app = flask_app.app
flask_app.add_api('swagger.yaml')

flask_app.app.before_request(before_request_handler)
# flask_app.app.secret_key = "".join(secrets.choice(string.ascii_letters + string.digits + '_' + '-' + '!' + '#' + '&') for i in range(64))


if __name__ == '__main__':
    flask_app.run(
        debug=True,
        host='0.0.0.0',
        port=int(os.environ.get('LISTEN_PORT', '8079')),
        threaded=True
    )
