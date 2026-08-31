import os
import subprocess
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# Global dictionary to keep track of running processes
processes = {}

SCRAPERS = {
    'cnc_machining': 'cnc_machining_scraper.py',
    'injection_molding': 'injection_molding_scraper.py',
    'mold_manufacturing': 'mold_manufacturing_scraper.py',
    'die_casting': 'die_casting_scraper.py',
    'company_scraper': 'company_scraper.py' # Optional, if they want to run deep scraper
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def get_status():
    status = {}
    for name in SCRAPERS.keys():
        proc = processes.get(name)
        if proc and proc.poll() is None:
            status[name] = 'running'
        else:
            status[name] = 'stopped'
    return jsonify(status)

@app.route('/api/start', methods=['POST'])
def start_scraper():
    data = request.json
    name = data.get('name')
    
    if not name or name not in SCRAPERS:
        return jsonify({'error': 'Invalid scraper name'}), 400
        
    proc = processes.get(name)
    if proc and proc.poll() is None:
        return jsonify({'message': f'{name} is already running'}), 200
        
    script_path = SCRAPERS[name]
    
    # Start process
    p = subprocess.Popen(
        ['python', script_path], 
        stdout=subprocess.DEVNULL, 
        stderr=subprocess.DEVNULL
    )
    processes[name] = p
    
    return jsonify({'message': f'Started {name}'})

@app.route('/api/stop', methods=['POST'])
def stop_scraper():
    data = request.json
    name = data.get('name')
    
    if not name or name not in SCRAPERS:
        return jsonify({'error': 'Invalid scraper name'}), 400
        
    proc = processes.get(name)
    if proc and proc.poll() is None:
        proc.terminate()
        proc.wait()
        return jsonify({'message': f'Stopped {name}'})
        
    return jsonify({'message': f'{name} is not running'}), 200

@app.route('/api/stats', methods=['GET'])
def get_stats():
    links_file = 'links.md'
    total_links = 0
    recent_links = []
    
    if os.path.exists(links_file):
        with open(links_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip() and line.strip() != '---']
            
        total_links = len(lines)
        recent_links = lines[-10:] # Get last 10 extracted links
        recent_links.reverse()
        
    return jsonify({
        'total_links': total_links,
        'target': 20000,
        'recent_links': recent_links
    })

@app.route('/api/logs/<name>', methods=['GET'])
def get_logs(name):
    if name not in SCRAPERS:
        return jsonify({'error': 'Invalid scraper name'}), 400
        
    log_file = f'logs/{name}_log.md'
    if not os.path.exists(log_file):
        return jsonify({'logs': 'No logs yet.'})
        
    # Read the last 50 lines
    with open(log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        tail = lines[-50:]
        
    return jsonify({'logs': "".join(tail)})

if __name__ == '__main__':
    # Run on all interfaces so Docker can expose it
    app.run(host='0.0.0.0', port=5000, debug=True)
