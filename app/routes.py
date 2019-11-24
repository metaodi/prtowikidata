from app import app
from flask import Flask, request, jsonify
import os
from github import Github
import base64
import hashlib
import hmac
import json
from dotenv import load_dotenv

load_dotenv()


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['success'] = False
        rv['message'] = self.message
        return rv


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route('/')
@app.route('/index')
def index():
    return "Hello, World!"


@app.route('/payload', methods=['POST'])
def parse_request():
    event = request.headers.get('X-GitHub-Event')
    gh_sig = request.headers.get('X-Hub-Signature')
    data = request.json

    print(request.headers)

    # if not validate_signature(request.get_data(), gh_sig):
    #    raise InvalidUsage('Wrong secret', status_code=401)

    if event != 'push':
        raise InvalidUsage('Invalid event, failed successfully :)', status_code=400)

    file_of_push = []
    file_of_push.extend(data['head_commit']['added'])
    file_of_push.extend(data['head_commit']['modified'])

    if 'goshmap2.csv' in file_of_push:
        g = Github(os.getenv('GITHUB_ACCESS_TOKEN'))
        repo = g.get_repo(data['repository']['full_name'])
        goshmap = repo.get_contents("goshmap2.csv")
        content = base64.b64decode(goshmap.content)
        print(content)
        return jsonify({'success': True})
    else:
        return jsonify({'success': True, 'message': 'No relevant file in push'})


def validate_signature(payload, gh_sig):
    secret = os.getenv('GITHUB_WEBHOOK_SECRET')
    signature = hmac.new(
        str(secret),
        str(payload),
        hashlib.sha1
    ).hexdigest()

    return hmac.compare_digest(signature, gh_sig.split('=')[1])


if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    port = os.getenv('PORT', 5000)
    print(port)
    app.run(threaded=True, port=port)
