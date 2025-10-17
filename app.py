import os
import subprocess
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'ec25d878b48e514cf2ec30439846000a'  # इसे एक मजबूत सीक्रेट की से बदलें
LOGIN_ACCESS_CODE = "DPX1432"
BOTS_DIR = "bots"

# सुनिश्चित करें कि 'bots' डायरेक्टरी मौजूद है
if not os.path.exists(BOTS_DIR):
    os.makedirs(BOTS_DIR)

# बॉट प्रक्रियाओं को ट्रैक करने के लिए एक डिक्शनरी
bot_processes = {}

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        access_code = request.form.get('access_code')
        if access_code == LOGIN_ACCESS_CODE:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            flash('गलत एक्सेस कोड!', 'error')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    bots = []
    for bot_name in os.listdir(BOTS_DIR):
        bot_path = os.path.join(BOTS_DIR, bot_name)
        if os.path.isdir(bot_path):
            status = "Running" if bot_name in bot_processes else "Stopped"
            bots.append({'name': bot_name, 'status': status})
            
    return render_template('index.html', bots=bots)

@app.route('/upload', methods=['POST'])
def upload_bot():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    bot_name = request.form.get('bot_name')
    bot_file = request.files.get('bot_file')
    req_file = request.files.get('req_file')

    if not bot_name or not bot_file or not req_file:
        flash('बॉट का नाम, bot.py और requirements.txt फ़ाइलें ज़रूरी हैं!', 'error')
        return redirect(url_for('index'))

    bot_dir = os.path.join(BOTS_DIR, bot_name)
    if not os.path.exists(bot_dir):
        os.makedirs(bot_dir)

    bot_file.save(os.path.join(bot_dir, 'bot.py'))
    req_file.save(os.path.join(bot_dir, 'requirements.txt'))

    flash(f'बॉट "{bot_name}" सफलतापूर्वक अपलोड हो गया!', 'success')
    return redirect(url_for('index'))

@app.route('/bot/<action>/<bot_name>', methods=['POST'])
def manage_bot(action, bot_name):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    bot_dir = os.path.join(BOTS_DIR, bot_name)
    bot_script = os.path.join(bot_dir, 'bot.py')

    if action == 'run':
        # पहले से चल रहा है या नहीं, जांचें
        if bot_name in bot_processes:
            flash(f'बॉट "{bot_name}" पहले से ही चल रहा है।', 'warning')
            return redirect(url_for('index'))

        try:
            # Requirements इंस्टॉल करें
            req_path = os.path.join(bot_dir, 'requirements.txt')
            subprocess.run(['pip', 'install', '-r', req_path], check=True)
            
            # बॉट को एक नई प्रक्रिया में चलाएं
            process = subprocess.Popen(['python', bot_script], cwd=bot_dir)
            bot_processes[bot_name] = process
            flash(f'बॉट "{bot_name}" शुरू हो गया है!', 'success')
        except Exception as e:
            flash(f'बॉट "{bot_name}" शुरू करने में त्रुटि: {e}', 'error')

    elif action == 'stop':
        if bot_name in bot_processes:
            bot_processes[bot_name].terminate()
            bot_processes.pop(bot_name)
            flash(f'बॉट "{bot_name}" बंद कर दिया गया है।', 'success')
        else:
            flash(f'बॉट "{bot_name}" नहीं चल रहा है।', 'warning')
            
    elif action == 'restart':
        if bot_name in bot_processes:
            bot_processes[bot_name].terminate()
            bot_processes.pop(bot_name)
        
        try:
            req_path = os.path.join(bot_dir, 'requirements.txt')
            subprocess.run(['pip', 'install', '-r', req_path], check=True)
            process = subprocess.Popen(['python', bot_script], cwd=bot_dir)
            bot_processes[bot_name] = process
            flash(f'बॉट "{bot_name}" फिर से शुरू हो गया है!', 'success')
        except Exception as e:
            flash(f'बॉट "{bot_name}" को फिर से शुरू करने में त्रुटि: {e}', 'error')

    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
