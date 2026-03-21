"""Route definitions for music_assistant_api (ma_routes).

This module registers the HTTP endpoints on a provided Flask
`Blueprint`. It stores the last pushed stream metadata in a
module-level `_store` variable.
"""

import re
import os
from flask import jsonify, request


_store = None


def register_routes(bp):
    @bp.route('/push-url', methods=['POST'])
    def push_url():
        """Accept JSON with streamUrl and optional metadata and store it.

        Expected JSON body: { streamUrl, title, artist, album, imageUrl }
        """
        global _store
        data = request.get_json(silent=True) or {}
        stream_url = data.get('streamUrl')
        if not stream_url:
            return jsonify({'error': 'Missing required fields'}), 400

        # On force le HTTPS et on retire le port 8097 
        # pour que ça passe par le port 443 de Nginx
        stream_url = stream_url.replace("http://", "https://")
        stream_url = stream_url.replace(":8097", "")
        
        # On remplace l'IP brute par le hostname public (STREAM_HOSTNAME) s'il est défini
        stream_hostname = os.environ.get('STREAM_HOSTNAME', '').strip().strip('"\' ')
        if stream_hostname:
            if not stream_hostname.startswith('http'):
                stream_hostname = f'https://{stream_hostname}'
            try:
                stream_url = re.sub(r'^https?://\d+\.\d+\.\d+\.\d+(?::\d+)?', stream_hostname, stream_url)
            except re.error:
                pass

        _store = {
            'streamUrl': stream_url,
            'title': data.get('title'),
            'artist': data.get('artist'),
            'album': data.get('album'),
            'imageUrl': data.get('imageUrl'),
        }
        print('Received:', _store)
        return jsonify({'status': 'ok'})

    @bp.route('/latest-url', methods=['GET'])
    def latest_url_ma():
        """Return the last pushed stream metadata for the Music Assistant.
        """
        if not _store:
            return jsonify({'error': 'No URL available, please check if Music Assistant has pushed a URL to the API'}), 404
        return jsonify(_store)
