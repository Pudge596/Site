import requests
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import re

app = Flask(__name__)

# Настройки приложения
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123@localhost/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Модель пользователя
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Список 20 игр (пример данных)
GAMES = [
    {"id": 730, "name": "Counter-Strike 2", "icon": "https://cdn.cloudflare.steamstatic.com/steam/apps/730/header.jpg", "description": "Многопользователький тактический шутер от первого лица."},
    {"id": 570, "name": "Dota 2", "icon": "https://cdn.cloudflare.steamstatic.com/steam/apps/570/header.jpg", "description": "Многопользовательская командная компьютерная игра в жанре MOBA."},
    {"id": 440, "name": "Team Fortress 2", "icon": "https://cdn.cloudflare.steamstatic.com/steam/apps/440/header.jpg", "description": "Многопользовательский шутер от первого лица."},
    {"id": 271590, "name": "Grand Theft Auto V", "icon": "https://cdn.cloudflare.steamstatic.com/steam/apps/271590/header.jpg", "description": "Компьютерная игра в жанре action-adventure с открытым миром."},
    {"id": 578080, "name": "PUBG: Battlegrounds", "icon": "https://cdn.cloudflare.steamstatic.com/steam/apps/578080/header.jpg", "description": "Многопользовательская видеоигра в жанре королевской битвы."},
    {"id": 292030, "name": "The Witcher 3: Wild Hunt", "icon": "https://cdn.cloudflare.steamstatic.com/steam/apps/292030/header.jpg", "description": "Компьютерная игра в жанре action/RPG."},
    {"id": 812140, "name": "Assassin's Creed Odyssey", "icon": "https://cdn.cloudflare.steamstatic.com/steam/apps/812140/header.jpg", "description": "Компьютерная игра в жанре Action/RPG."},
    {"id": 413150, "name": "Stardew Valley", "icon": "https://cdn.cloudflare.steamstatic.com/steam/apps/413150/header.jpg", "description": "Компьютерная игра в жанре симулятора жизни фермера с элементами ролевой игры."},
    {"id": 346110, "name": "ARK: Survival Evolved", "icon": "https://cdn.cloudflare.steamstatic.com/steam/apps/346110/header.jpg", "description": "Выживание среди динозавров."},
    {"id": 1063730, "name": "New World: Aeternum", "icon": "https://cdn.cloudflare.steamstatic.com/steam/apps/1063730/header.jpg", "description": "Многопользовательский экшен."},
    {"id": 252490, "name": "Rust", "icon": "https://cdn.cloudflare.steamstatic.com/steam/apps/252490/header.jpg", "description": "Выживание в суровом мире."},
    {"id": 1091500, "name": "Cyberpunk 2077", "icon": "https://cdn.cloudflare.steamstatic.com/steam/apps/1091500/header.jpg", "description": "Будущее в стиле киберпанк."},
    {"id": 1245620, "name": "Elden Ring", "icon": "https://cdn.cloudflare.steamstatic.com/steam/apps/1245620/header.jpg", "description": "Компьютерная игра в жанре Action/RPG."},
    {"id": 393380, "name": "Squad", "icon": "https://cdn.cloudflare.steamstatic.com/steam/apps/393380/header.jpg", "description": "Тактический шутер с реализмом."},
    {"id": 1085660, "name": "Destiny 2", "icon": "https://cdn.cloudflare.steamstatic.com/steam/apps/1085660/header.jpg", "description": "Эпический шутер в стиле sci-fi."},
    {"id": 271590, "name": "Garry's Mod", "icon": "https://cdn.cloudflare.steamstatic.com/steam/apps/4000/header.jpg", "description": "Песочница без границ."},
    {"id": 292030, "name": "The Forest", "icon": "https://cdn.cloudflare.steamstatic.com/steam/apps/242760/header.jpg", "description": "Выживание в жутком лесу."},
    {"id": 8930, "name": "Sid Meier's Civilization V", "icon": "https://cdn.cloudflare.steamstatic.com/steam/apps/8930/header.jpg", "description": "Построй свою цивилизацию."},
    {"id": 381210, "name": "Dead by Daylight", "icon": "https://cdn.cloudflare.steamstatic.com/steam/apps/381210/header.jpg", "description": "Многопользовательская компьютерная игра в жанре survival horror."},
    {"id": 582010, "name": "Monster Hunter: World", "icon": "https://cdn.cloudflare.steamstatic.com/steam/apps/582010/header.jpg", "description": "Охота на гигантских монстров."},
]

# Получение новостей из Steam API
def get_game_updates(appid):
    url = f'https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/'

    params = {
        'appid': appid,
        'count': 20
    }
    response = requests.get(url, params=params)
    data = response.json()
    news_items = data.get('appnews', {}).get('newsitems', [])
    for item in news_items:
        item['date'] = datetime.utcfromtimestamp(item['date']).strftime('%d %B %Y, %H:%M')
    return news_items

# Главная страница (без авторизации)
@app.route("/")
def index():
    query = request.args.get("q", "").lower()
    filtered_games = [game for game in GAMES if query in game["name"].lower()]
    return render_template("index.html", games=filtered_games, query=query, user=current_user)

# Страница игры (без авторизации)
@app.route("/game/<int:game_id>")
def game_page(game_id):
    game = next((g for g in GAMES if g['id'] == game_id), None)
    if not game:
        return "Game not found", 404

    query = request.args.get("q", "").lower()
    updates = get_game_updates(game['id'])
    filtered_updates = []
    for update in updates:
        cleaned_content = re.sub(r'\[.*?\]', '', update['contents']).strip()
        cleaned_content = re.sub(r'<img[^>]*>', '', cleaned_content).strip()
        cleaned_content = re.sub(r'\{STEAM_CLAN_IMAGE\}[^ ]*\.png', '', cleaned_content).strip()
        if query in cleaned_content.lower():
            update['contents'] = cleaned_content
            filtered_updates.append(update)
    return render_template('game_page.html', game=game, updates=filtered_updates)

# Регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            return "Пароли не совпадают", 400

        if User.query.filter_by(username=username).first():
            return "Пользователь с таким логином уже существует!", 400

        # Использование метода pbkdf2:sha256
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/login')

    return render_template('register.html')


# Авторизация
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect('/')

        return "Неверные учетные данные", 400

    return render_template('login.html')

# Выход
@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect('/')

# Инициализация базы данных (однократно)
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
