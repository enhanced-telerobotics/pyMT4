import numpy as np
from pyMT4 import MTC
from flask import Flask, jsonify, request

# Initialize the global MTC object
mtc = None

def create_app():
    app = Flask(__name__)

    @app.route('/api/get_pose', methods=['GET'])
    def get_resource():
        if mtc is None:
            return jsonify({"error": "MTC not initialized"}), 500
        
        # Get data from the request
        rot = request.args.get('rot', 'false').lower() == 'true'
        
        # Get the current pose data
        data = mtc.get_poses(rot)
        data = ndarray_to_list(data)

        return jsonify(data), 200

    return app

def main():
    global mtc
    mtc = MTC()
    # Warm up the device
    for _ in range(10):
        mtc.get_poses()

    app = create_app()
    # Start the Flask server without reloader to prevent multiple processes
    app.run(debug=False, use_reloader=False, host='0.0.0.0', port=18080)

def ndarray_to_list(data):
    """
    Recursively convert all numpy arrays in the data to lists.
    Handles dictionaries, lists, and numpy arrays.
    """
    if isinstance(data, dict):
        return {key: ndarray_to_list(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [ndarray_to_list(element) for element in data]
    elif isinstance(data, np.ndarray):
        return data.tolist()
    else:
        return data

if __name__ == "__main__":
    main()