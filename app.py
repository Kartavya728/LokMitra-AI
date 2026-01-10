from flask import Flask, render_template, Response, jsonify
import cv2
import threading
import time
import os
from ekyc import EKYCVerifier

app = Flask(__name__)

# Global state
class AppState:
    def __init__(self):
        self.camera = None
        self.is_recording = False
        self.recording_start_time = 0
        self.recording_duration = 15
        self.video_writer = None
        self.video_path = "images/web_record.avi"
        self.latest_frame = None
        self.status = "idle" # idle, recording, processing, completed, failed
        self.result = {}
        self.lock = threading.Lock()

    def get_camera(self):
        if self.camera is None or not self.camera.isOpened():
            self.camera = cv2.VideoCapture(0)
        return self.camera

    def release_camera(self):
        if self.camera:
            self.camera.release()
            self.camera = None

state = AppState()
verifier = EKYCVerifier()

# Ensure images dir exists
os.makedirs("images", exist_ok=True)

def generate_frames():
    global state
    
    while True:
        cam = state.get_camera()
        success, frame = cam.read()
        
        if not success:
            time.sleep(0.1)
            continue

        # Logic for Recording / Instructions
        with state.lock:
            current_status = state.status

        if current_status == "recording":
            elapsed = time.time() - state.recording_start_time
            if elapsed < state.recording_duration:
                # Write to video
                if state.video_writer:
                    state.video_writer.write(frame)
                
                # Overlay Instructions
                remaining = int(state.recording_duration - elapsed)
                msg = f"Look Center -> Left -> Right ({remaining}s)"
                # Frame is BGR, usually we stream BGR to jpg. 
                # Note: 'frame' is mutable. We should copy if we don't want to burn text into the saved video? 
                # Actually, ekyc.py usually runs on raw frames. 
                # If we burn text into saved video, detection might suffer? 
                # Better to burn text ONLY on the display copy.
                
                display_frame = frame.copy()
                cv2.putText(display_frame, msg, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                
                ret, buffer = cv2.imencode('.jpg', display_frame)
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                # Recording Finished
                with state.lock:
                    state.is_recording = False
                    state.status = "processing"
                    if state.video_writer:
                        state.video_writer.release()
                        state.video_writer = None
                
                # Trigger processing in background thread
                threading.Thread(target=process_verification).start()

        else:
            # Just streaming
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

def process_verification():
    global state
    try:
        print("Processing verification...")
        # 1. Liveness
        video_path = state.video_path
        selfie_path = verifier.liveness_check(video_path)
        
        if not selfie_path:
            with state.lock:
                state.status = "completed"
                state.result = {"verified": False, "reason": "Liveness Check Failed (Did not detect all movements)"}
            return

        # 2. Identity
        # fetch ID card logic is inside verify_identity, but we need to break it apart slightly 
        # or just trust verify_identity to do it all if we pass the selfie?
        # The current verify_identity calls record_video. We need to bypass that.
        # Let's call the components manually since we have the selfie path now.
        
        print("Fetching ID...")
        try:
            id_path = verifier.fetch_latest_id_card()
        except:
             id_path = "images/id_card.jpg" # Fallback
        
        print(f"Extracting face from {id_path}")
        extracted_face = verifier.extract_face_from_id(id_path)
        
        print("Running DeepFace verify...")
        result = verifier.verify_identity_with_images(extracted_face, selfie_path)
        
        with state.lock:
            state.status = "completed"
            state.result = result

    except Exception as e:
        print(f"Error processing: {e}")
        with state.lock:
            state.status = "failed"
            state.result = {"error": str(e)}

# Monkey patch or extend EKYCVerifier to support explicit image paths if needed
# Actually, looking at ekyc.py, verify_identity does everything.
# We should add a helper to EKYCVerifier to verify given two paths, or just use DeepFace directly here.
# But ekyc.py has 'verify_identity' which does the whole flow. 
# Let's add a method to ekyc.py to verify generic images, or just use `DeepFace.verify` here directly 
# but that requires importing DeepFace here. `ekyc.py` already imports it.
# Let's add a helper code block to `app.py` that acts as the bridge.
# Wait, I'll add `verify_identity_with_images` to `ekyc.py` quickly or just import DeepFace in app.py.
# Using `verifier.verify_identity` is hard because it calls `record_video` internally.
# I will use DeepFace directly in app.py for the final step, since `verifier` instance has the localized logic.
# Actually, better to modify `ekyc.py` to allow passing `selfie_path` to `verify_identity`.
# But for now, I'll just replicate the verify call in `process_verification` above.
# I need to import DeepFace in app.py? Or just put a method in ekyc.py?
# Let's put a method in ekyc.py via edit, it's cleaner.

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/start_process')
def start_process():
    global state
    with state.lock:
        if state.status == "recording":
             return jsonify({"status": "already_started"})
        
        state.status = "recording"
        state.recording_start_time = time.time()
        state.is_recording = True
        
        # Init Video Writer
        cam = state.get_camera()
        w = int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = 30.0
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        state.video_writer = cv2.VideoWriter(state.video_path, fourcc, fps, (w, h))

    return jsonify({"status": "started"})

@app.route('/get_result')
def get_result():
    global state
    with state.lock:
        data = {
            "status": state.status,
            "result": state.result,
        }
        if state.status == "recording":
             elapsed = time.time() - state.recording_start_time
             data["time_left"] = int(max(0, state.recording_duration - elapsed))
             
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
