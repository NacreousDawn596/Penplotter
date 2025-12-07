import sys
import os
import cv2
import numpy as np
import base64
import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS
import io
from PIL import Image
import tempfile
import shutil

# Add the project root to sys.path to allow importing penplotter modules
# When frozen, sys._MEIPASS contains the temp folder with bundled resources
if getattr(sys, 'frozen', False):
    project_root = sys._MEIPASS
else:
    # Current file is in webui/backend/
    # Project root is ../../
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))

sys.path.append(project_root)

try:
    import penplotter.img2sketch as img2sketch
    import penplotter.imageUtils as imageUtils
    import penplotter.interface as interface
except ImportError as e:
    print(f"Error importing penplotter modules: {e}")
    sys.exit(1)

# Board definitions
# Estimated bytes per point is rough. 
# Base sketch size is also rough (Stepper lib + overhead).
BOARDS = {
    'arduino:avr:uno': {'name': 'Arduino Uno', 'flash': 32256, 'base_size': 4000, 'bytes_per_point': 24},
    'arduino:avr:mega': {'name': 'Arduino Mega', 'flash': 253952, 'base_size': 4000, 'bytes_per_point': 24},
    'arduino:avr:nano': {'name': 'Arduino Nano', 'flash': 30720, 'base_size': 4000, 'bytes_per_point': 24},
    'esp32:esp32:esp32': {'name': 'ESP32', 'flash': 1310720, 'base_size': 200000, 'bytes_per_point': 20}, # 1.3MB app partition usually
}

# Global cache for the last processed image and params
LAST_PROCESSED_DATA = {
    'image': None, # numpy array (sketch result)
    'params': {}
}

# Global cache for the last compiled sketch directory
LAST_COMPILED_DIR = None

app = Flask(__name__)
CORS(app)

def estimate_size(contours, board_key):
    board = BOARDS.get(board_key, BOARDS['arduino:avr:uno'])
    total_points = sum(len(c) for c in contours)
    estimated = board['base_size'] + (total_points * board['bytes_per_point'])
    return estimated, total_points, board['flash']

@app.route('/api/boards', methods=['GET'])
def get_boards():
    return jsonify(BOARDS)

@app.route('/api/process', methods=['POST'])
def process_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No image selected'}), 400

    # Get parameters
    try:
        n = int(request.form.get('n', 0))
        canny_threshold1 = int(request.form.get('canny_threshold1', 125))
        canny_threshold2 = int(request.form.get('canny_threshold2', 130))
        pen_diameter = float(request.form.get('pen_diameter', 1.5))
        max_width = int(request.form.get('max_width', 2200))
        multiplier = int(request.form.get('multiplier', 6))
        # scale = float(request.form.get('scale', 0.4)) # Not used for raw contours return usually, but let's see
    except ValueError:
        return jsonify({'error': 'Invalid parameters'}), 400

    # Read image
    try:
        # Convert uploaded file to numpy array for cv2
        in_memory_file = io.BytesIO()
        file.save(in_memory_file)
        in_memory_file.seek(0)
        file_bytes = np.asarray(bytearray(in_memory_file.read()), dtype=np.uint8)
        frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        if frame is None:
             return jsonify({'error': 'Failed to decode image'}), 400

        # Process image
        i2s = img2sketch.PencilSketch()
        sketch_result = i2s(frame)
        
        if sketch_result is None:
            return jsonify({'error': 'Sketch generation failed'}), 500

        # Cache the sketch result for potential re-optimization
        LAST_PROCESSED_DATA['image'] = sketch_result
        LAST_PROCESSED_DATA['params'] = {
            'n': n,
            'canny_threshold1': canny_threshold1,
            'canny_threshold2': canny_threshold2,
            'pen_diameter': pen_diameter,
            'max_width': max_width,
            'multiplier': multiplier
        }

        contours = imageUtils.image_to_contours(
            img=sketch_result,
            n=n,
            canny_threshold1=canny_threshold1,
            canny_threshold2=canny_threshold2,
            pen_diameter=pen_diameter,
            max_width=max_width,
            multiplier=multiplier
        )
        
        # Convert contours to a JSON-friendly format
        # contours is a list of lists of points (x, y)
        # We need to serialize this.
        # Check structure of contours from imageUtils.py:
        # simplified_contours.append(scaled) -> scaled is list of (x, y)
        
        # Ensure data types are native Python types (int/float) not numpy types
        json_contours = []
        for contour in contours:
            json_contour = []
            for point in contour:
                json_contour.append([int(point[0]), int(point[1])])
            json_contours.append(json_contour)

        # Estimate memory usage
        board_key = request.form.get('fqbn', 'arduino:avr:uno')
        estimated_size, total_points, max_flash = estimate_size(contours, board_key)

        return jsonify({
            'contours': json_contours,
            'stats': {
                'estimated_size': estimated_size,
                'total_points': total_points,
                'flash': max_flash,
                'percent_usage': min(100, (estimated_size / max_flash) * 100)
            }
        })

    except Exception as e:
        print(f"Error processing image: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/compile', methods=['POST'])
def compile_code():
    global LAST_COMPILED_DIR
    try:
        data = request.json
        contours = data.get('contours')
        if not contours:
            return jsonify({'error': 'No contours provided'}), 400
            
        # Save to .ino file in a temporary directory
        # interface.save_polygons expects list of lists of tuples/lists
        # It saves to {name}.ino
        
        # Create a temp dir for this compilation
        # If we have a previous one, we could clean it up, but let's just make a new one
        if LAST_COMPILED_DIR and os.path.exists(LAST_COMPILED_DIR):
            try:
                shutil.rmtree(LAST_COMPILED_DIR)
            except Exception as e:
                print(f"Warning: Could not clean up old temp dir: {e}")

        temp_dir = tempfile.mkdtemp()
        LAST_COMPILED_DIR = temp_dir
        
        # Generate a unique filename for the sketch to avoid conflicts
        sketch_name = os.path.basename(temp_dir) 
        
        # We need to change cwd to temp_dir because save_polygons might write to cwd
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            
            import penplotter.interface as interface
            interface.save_polygons(sketch_name, contours) # Saves as {sketch_name}.ino in temp_dir
            
            # Compile
            fqbn = data.get('fqbn', 'arduino:avr:uno')
            print(fqbn)
            
            # arduino-cli compile --fqbn ... {sketch_name}.ino
            cmd = ['arduino-cli', 'compile', '--fqbn', fqbn, f'{sketch_name}.ino']
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                # Check for overflow error or size exceeded
                error_msg = result.stderr
                if ("overflowed by" in error_msg or "exceeds available space" in error_msg or "Sketch too big" in error_msg) and LAST_PROCESSED_DATA['image'] is not None:
                    print("Detected overflow, attempting auto-optimization...")
                    
                    # Optimization loop
                    current_params = LAST_PROCESSED_DATA['params'].copy()
                    sketch_result = LAST_PROCESSED_DATA['image']
                    
                    # Try up to 10 times
                    for i in range(10):
                        # Adjust parameters
                        current_params['canny_threshold1'] += 10
                        current_params['canny_threshold2'] += 10 # Keep gap
                        current_params['pen_diameter'] += 0.5
                        
                        print(f"Optimization attempt {i+1}: n={current_params['n']}, canny1={current_params['canny_threshold1']}")

                        contours = imageUtils.image_to_contours(
                            img=sketch_result,
                            n=current_params['n'],
                            canny_threshold1=current_params['canny_threshold1'],
                            canny_threshold2=current_params['canny_threshold2'],
                            pen_diameter=current_params['pen_diameter'],
                            max_width=current_params['max_width'],
                            multiplier=current_params['multiplier']
                        )
                        
                        # Save and retry compile
                        interface.save_polygons(filename, contours)
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        
                        if result.returncode == 0:
                            print("Optimization successful!")
                            
                            # Format new contours for frontend
                            json_contours = []
                            for contour in contours:
                                json_contour = []
                                for point in contour:
                                    json_contour.append([int(point[0]), int(point[1])])
                                json_contours.append(json_contour)
                                
                            est, pts, flash = estimate_size(contours, fqbn)
                            
                            return jsonify({
                                'message': 'Compilation successful after optimization', 
                                'output': result.stdout,
                                'optimized': True,
                                'new_params': current_params,
                                'new_contours': json_contours,
                                'new_stats': {
                                    'estimated_size': est,
                                    'total_points': pts,
                                    'flash': flash,
                                    'percent_usage': min(100, (est / flash) * 100)
                                }
                            })
                
                return jsonify({'error': 'Compilation failed', 'details': result.stderr}), 500
                
            return jsonify({'message': 'Compilation successful', 'output': result.stdout})
            
        finally:
            os.chdir(original_cwd)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_code():
    global LAST_COMPILED_DIR
    try:
        data = request.json
        port = data.get('port', '/dev/ttyACM0')
        fqbn = data.get('fqbn', 'arduino:avr:uno')
        
        if not LAST_COMPILED_DIR or not os.path.exists(LAST_COMPILED_DIR):
             return jsonify({'error': 'No compiled sketch found. Please compile first.'}), 400

        # Upload
        original_cwd = os.getcwd()
        try:
            os.chdir(LAST_COMPILED_DIR)
            filename = f"{os.path.basename(os.getcwd())}.ino"
            print(filename)
            # filename = "backend.ino"
        
            cmd = ['arduino-cli', 'upload', '-p', port, '--fqbn', fqbn, filename]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return jsonify({'error': 'Upload failed', 'details': result.stderr}), 500
                
            return jsonify({'message': 'Upload successful', 'output': result.stdout})
        finally:
            os.chdir(original_cwd)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/optimize', methods=['POST'])
def optimize_params():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    board_key = request.form.get('fqbn', 'arduino:avr:uno')
    
    # Initial params
    n = int(request.form.get('n', 0))
    canny1 = int(request.form.get('canny_threshold1', 125))
    canny2 = int(request.form.get('canny_threshold2', 130))
    pen_diameter = float(request.form.get('pen_diameter', 1.5))
    max_width = int(request.form.get('max_width', 2200))
    multiplier = int(request.form.get('multiplier', 6))

    # Read image once
    in_memory_file = io.BytesIO()
    file.save(in_memory_file)
    in_memory_file.seek(0)
    file_bytes = np.asarray(bytearray(in_memory_file.read()), dtype=np.uint8)
    frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    i2s = img2sketch.PencilSketch()
    sketch_result = i2s(frame)
    
    if sketch_result is None:
        return jsonify({'error': 'Sketch generation failed'}), 500

    # Optimization loop
    # We want usage < 95% to be safe
    target_usage = 0.95
    
    best_contours = []
    best_params = {}
    
    # Try increasing n (simplification)
    for test_n in range(n, 20, 2):
        contours = imageUtils.image_to_contours(
            img=sketch_result,
            n=test_n,
            canny_threshold1=canny1,
            canny_threshold2=canny2,
            pen_diameter=pen_diameter,
            max_width=max_width,
            multiplier=multiplier
        )
        
        est, _, flash = estimate_size(contours, board_key)
        usage = est / flash
        
        if usage <= target_usage:
            # Found a fit!
            best_contours = contours
            best_params = {
                'n': test_n,
                'canny_threshold1': canny1,
                'canny_threshold2': canny2
            }
            break
            
    # If still too big, try increasing canny thresholds to reduce detail
    if not best_params:
        test_n = 10 # Start with high simplification
        for test_c1 in range(canny1, 200, 10):
            contours = imageUtils.image_to_contours(
                img=sketch_result,
                n=test_n,
                canny_threshold1=test_c1,
                canny_threshold2=canny2 + (test_c1 - canny1), # Keep gap roughly same
                pen_diameter=pen_diameter,
                max_width=max_width,
                multiplier=multiplier
            )
            
            est, _, flash = estimate_size(contours, board_key)
            usage = est / flash
            
            if usage <= target_usage:
                best_contours = contours
                best_params = {
                    'n': test_n,
                    'canny_threshold1': test_c1,
                    'canny_threshold2': canny2 + (test_c1 - canny1)
                }
                break

    if not best_params:
        return jsonify({'error': 'Could not optimize to fit on board. Try a simpler image.'}), 400

    # Format contours
    json_contours = []
    for contour in best_contours:
        json_contour = []
        for point in contour:
            json_contour.append([int(point[0]), int(point[1])])
        json_contours.append(json_contour)
        
    est, pts, flash = estimate_size(best_contours, board_key)

    return jsonify({
        'contours': json_contours,
        'params': best_params,
        'stats': {
            'estimated_size': est,
            'total_points': pts,
            'flash': flash,
            'percent_usage': min(100, (est / flash) * 100)
        }
    })

if __name__ == '__main__':
    app.run(debug=True, port=3030)
