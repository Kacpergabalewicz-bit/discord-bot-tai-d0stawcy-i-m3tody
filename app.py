from flask import Flask, render_template, request, session, redirect, url_for
from database import get_user_history, get_all_data, init_db
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = 'Meteoryt07!'

# Sesja wygasa co sekundę
app.permanent_session_lifetime = timedelta(seconds=1)

# Admin credentials
ADMIN_EMAIL = "kacper.gabalewicz@gmail.com"
ADMIN_PASSWORD = "Meteoryt07!"

# Inicjalizuj bazę
init_db()

@app.before_request
def mark_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=5)

@app.route('/')
def index():
    if 'logged_in' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            session['email'] = email
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="❌ Email lub hasło nieprawidłowe!")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    data = get_all_data()
    
    stats = {
        'opinions': len(data['opinions']) if data['opinions'] else 0,
        'verifications': len(data['verifications']) if data['verifications'] else 0,
        'bans': len(data['bans']) if data['bans'] else 0,
        'mutes': len(data['mutes']) if data['mutes'] else 0,
    }
    
    return render_template('dashboard.html', stats=stats, data=data)

@app.route('/user/<username>')
def user_history(username):
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    history = get_user_history(username)
    
    if history is None or (not history['opinions'] and not history['verifications'] 
                          and not history['bans'] and not history['mutes']):
        return render_template('user_history.html', username=username, found=False)
    
    return render_template('user_history.html', username=username, found=True, history=history)

@app.route('/search', methods=['GET'])
def search():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    query = request.args.get('query', '').strip()
    
    if not query:
        return redirect(url_for('dashboard'))
    
    return redirect(url_for('user_history', username=query))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Panel uruchamiany na http://0.0.0.0:{port}")
    print(f"📧 Email: {ADMIN_EMAIL}")
    print(f"🔑 Hasło: {ADMIN_PASSWORD}")
    app.run(debug=False, host='0.0.0.0', port=port)
