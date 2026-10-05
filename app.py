import os
import sys

# Ensure the deepfake_detector package directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGE_DIR = os.path.join(BASE_DIR, 'deepfake_detector')

if PACKAGE_DIR not in sys.path:
    sys.path.insert(0, PACKAGE_DIR)

# Import the configured Flask instance
from app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8500))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    # Bind to 0.0.0.0 for web hosting and container deployment
    app.run(host='0.0.0.0', port=port, debug=debug)
