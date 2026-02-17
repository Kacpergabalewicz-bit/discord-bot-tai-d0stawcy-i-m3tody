import sqlite3
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "discord_bot.db")

def init_db():
    """Tworzy bazę danych i tabele"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabela opinii
    cursor.execute('''CREATE TABLE IF NOT EXISTS opinions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        product TEXT,
        realization TEXT,
        stars INTEGER,
        recommend TEXT,
        date TEXT
    )''')
    
    # Tabela weryfikacji
    cursor.execute('''CREATE TABLE IF NOT EXISTS verifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        age INTEGER,
        date TEXT
    )''')
    
    # Tabela banów
    cursor.execute('''CREATE TABLE IF NOT EXISTS bans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        admin_id INTEGER,
        reason TEXT,
        date TEXT
    )''')
    
    # Tabela mutów
    cursor.execute('''CREATE TABLE IF NOT EXISTS mutes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        admin_id INTEGER,
        reason TEXT,
        date TEXT
    )''')
    
    conn.commit()
    conn.close()
    print("✅ Baza danych zainicjalizowana!")

def log_opinion(user_id, username, product, realization, stars, recommend):
    """Loguje opinię do bazy"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        date = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        cursor.execute('''INSERT INTO opinions 
                         (user_id, username, product, realization, stars, recommend, date)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (user_id, username, product, realization, stars, recommend, date))
        conn.commit()
        conn.close()
        print(f"✅ Opinia użytkownika {username} zapisana!")
        return True
    except Exception as e:
        print(f"❌ Błąd przy logowaniu opinii: {e}")
        return False

def log_verification(user_id, username, age):
    """Loguje weryfikację do bazy"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        date = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        cursor.execute('''INSERT INTO verifications 
                         (user_id, username, age, date)
                         VALUES (?, ?, ?, ?)''',
                      (user_id, username, age, date))
        conn.commit()
        conn.close()
        print(f"✅ Weryfikacja użytkownika {username} zapisana!")
        return True
    except Exception as e:
        print(f"❌ Błąd przy logowaniu weryfikacji: {e}")
        return False

def log_ban(user_id, username, admin_id, reason):
    """Loguje bana do bazy"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        date = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        cursor.execute('''INSERT INTO bans 
                         (user_id, username, admin_id, reason, date)
                         VALUES (?, ?, ?, ?, ?)''',
                      (user_id, username, admin_id, reason, date))
        conn.commit()
        conn.close()
        print(f"✅ Ban użytkownika {username} zapisany!")
        return True
    except Exception as e:
        print(f"❌ Błąd przy logowaniu bana: {e}")
        return False

def log_mute(user_id, username, admin_id, reason):
    """Loguje mute do bazy"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        date = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        cursor.execute('''INSERT INTO mutes 
                         (user_id, username, admin_id, reason, date)
                         VALUES (?, ?, ?, ?, ?)''',
                      (user_id, username, admin_id, reason, date))
        conn.commit()
        conn.close()
        print(f"✅ Mute użytkownika {username} zapisany!")
        return True
    except Exception as e:
        print(f"❌ Błąd przy logowaniu mute: {e}")
        return False

def get_user_history(username):
    """Pobiera całą historię użytkownika"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Opinii
        cursor.execute("SELECT * FROM opinions WHERE username = ?", (username,))
        opinions = cursor.fetchall()
        
        # Weryfikacje
        cursor.execute("SELECT * FROM verifications WHERE username = ?", (username,))
        verifications = cursor.fetchall()
        
        # Bany
        cursor.execute("SELECT * FROM bans WHERE username = ?", (username,))
        bans = cursor.fetchall()
        
        # Muty
        cursor.execute("SELECT * FROM mutes WHERE username = ?", (username,))
        mutes = cursor.fetchall()
        
        conn.close()
        
        return {
            'opinions': opinions,
            'verifications': verifications,
            'bans': bans,
            'mutes': mutes
        }
    except Exception as e:
        print(f"❌ Błąd przy pobieraniu historii: {e}")
        return None

def get_all_data():
    """Pobiera wszystkie dane z bazy"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM opinions")
        opinions = cursor.fetchall()
        
        cursor.execute("SELECT * FROM verifications")
        verifications = cursor.fetchall()
        
        cursor.execute("SELECT * FROM bans")
        bans = cursor.fetchall()
        
        cursor.execute("SELECT * FROM mutes")
        mutes = cursor.fetchall()
        
        conn.close()
        
        return {
            'opinions': opinions,
            'verifications': verifications,
            'bans': bans,
            'mutes': mutes
        }
    except Exception as e:
        print(f"❌ Błąd: {e}")
        return None

# Inicjalizuj bazę przy imporcie
if not os.path.exists(DB_PATH):
    init_db()
