"""HTTP server for a single MicronTracker device."""
import argparse
import logging
from threading import Lock

import numpy as np
from flask import Flask, jsonify, request
from .mtc import MTC


def ndarray_to_list(data):
    """Convert nested NumPy values into JSON-compatible values."""
    if isinstance(data, dict):
        return {key: ndarray_to_list(value) for key, value in data.items()}
    if isinstance(data, (list, tuple)):
        return [ndarray_to_list(value) for value in data]
    if isinstance(data, np.ndarray):
        return ndarray_to_list(data.tolist())
    if isinstance(data, np.generic):
        return data.item()
    return data


class TrackerService:
    """Serialize acquisition and shutdown of the shared native device."""
    def __init__(self, tracker):
        self.tracker = tracker
        self.lock = Lock()
        self.closed = False

    def get_poses(self, rot):
        with self.lock:
            if self.closed:
                raise RuntimeError('Tracker is closed')
            return ndarray_to_list(self.tracker.get_poses(rot))

    def close(self):
        with self.lock:
            if not self.closed:
                self.closed = True
                self.tracker.close()


def create_app(tracker):
    """Build an app around an initialized tracker; caller owns its lifetime."""
    app = Flask(__name__)
    service = TrackerService(tracker)
    app.extensions['tracker_service'] = service

    @app.get('/api/get_pose')
    def get_pose():
        rot = request.args.get('rot', 'false').lower()
        if rot not in ('true', 'false'):
            return jsonify(error="rot must be 'true' or 'false'"), 400
        try:
            return jsonify(service.get_poses(rot == 'true'))
        except Exception:
            app.logger.exception('Failed to acquire tracker poses')
            return jsonify(error='Tracker acquisition failed'), 503

    @app.after_request
    def disable_cache(response):
        response.headers['Cache-Control'] = 'no-store'
        return response

    return app


def main(argv=None):
    """Initialize the tracker once and serve until interrupted."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=18080)
    parser.add_argument('--warmup-frames', type=int, default=10)
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error('--port must be between 1 and 65535')
    if args.warmup_frames < 0:
        parser.error('--warmup-frames must be nonnegative')

    from waitress import serve
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    tracker = MTC()
    service = None
    try:
        for _ in range(args.warmup_frames):
            tracker.get_poses()
        app = create_app(tracker)
        service = app.extensions['tracker_service']
        serve(app, host=args.host, port=args.port, threads=4)
    except KeyboardInterrupt:
        logging.info('Stopping tracker server')
    finally:
        if service is not None:
            service.close()
        else:
            tracker.close()


if __name__ == '__main__':
    main()
