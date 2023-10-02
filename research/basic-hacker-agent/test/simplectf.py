from flask import Flask, request, render_template_string
import sqlite3

app = Flask(__name__)

# Initialize SQLite database with a flag
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT);''')
    c.execute('''INSERT INTO users (username, password) VALUES ('admin', 'FLAG{sql_injection_is_dangerous}');''')
    conn.commit()
    conn.close()

init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute(f"SELECT * FROM users WHERE username='{username}' AND password='{password}'")
        data = c.fetchone()
        conn.close()

        if data:
            return f"Logged in as {data[0]}"

    return '''
    <form method="post">
        Username: <input type="text" name="username"><br>
        Password: <input type="password" name="password"><br>
        <input type="submit" value="Login">
    </form>
    '''

if __name__ == '__main__':
    app.run(debug=True)
