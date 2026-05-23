import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os

# ------------------ НАСТРОЙКА СТРАНИЦЫ ------------------
st.set_page_config(page_title="Учёт командировок", layout="wide")
st.title("📋 Учёт командировок сотрудников")

# ------------------ РАБОТА С БАЗОЙ ДАННЫХ ------------------
DB_NAME = "trips.db"

def init_db():
    """Создаёт таблицы, если их нет, и добавляет тестовых пользователей"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  login TEXT UNIQUE,
                  password TEXT,
                  full_name TEXT,
                  role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS trips
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  city TEXT,
                  start_date TEXT,
                  end_date TEXT,
                  purpose TEXT,
                  planned_costs REAL,
                  status TEXT DEFAULT 'На рассмотрении',
                  report_file TEXT,
                  created_at TEXT,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    # Добавляем тестовых пользователей, только если таблица пуста
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users (login, password, full_name, role) VALUES (?,?,?,?)",
                  ("ivanov", "123", "Иван Иванов", "employee"))
        c.execute("INSERT INTO users (login, password, full_name, role) VALUES (?,?,?,?)",
                  ("admin", "admin", "Администратор", "admin"))
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    return sqlite3.connect(DB_NAME)

# ------------------ АВТОРИЗАЦИЯ И РЕГИСТРАЦИЯ ------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.role = None
    st.session_state.full_name = None

def register():
    st.sidebar.header("📝 Регистрация нового пользователя")
    with st.sidebar.form("registration_form"):
        new_login = st.text_input("Логин")
        new_password = st.text_input("Пароль", type="password")
        new_full_name = st.text_input("ФИО")
        new_role = st.selectbox("Роль", ["employee", "admin"])
        submitted = st.form_submit_button("Зарегистрироваться")
        if submitted:
            if not new_login or not new_password or not new_full_name:
                st.sidebar.error("Заполните все поля")
            else:
                conn = get_db_connection()
                c = conn.cursor()
                try:
                    c.execute("INSERT INTO users (login, password, full_name, role) VALUES (?,?,?,?)",
                              (new_login, new_password, new_full_name, new_role))
                    conn.commit()
                    st.sidebar.success(f"Пользователь {new_login} создан! Теперь войдите.")
                except sqlite3.IntegrityError:
                    st.sidebar.error("Такой логин уже существует")
                finally:
                    conn.close()

def login():
    st.sidebar.header("🔐 Вход в систему")
    login_input = st.sidebar.text_input("Логин")
    password_input = st.sidebar.text_input("Пароль", type="password")
    if st.sidebar.button("Войти"):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT id, full_name, role FROM users WHERE login=? AND password=?", (login_input, password_input))
        user = c.fetchone()
        conn.close()
        if user:
            st.session_state.logged_in = True
            st.session_state.user_id = user[0]
            st.session_state.full_name = user[1]
            st.session_state.role = user[2]
            st.success(f"Добро пожаловать, {user[1]}!")
            st.rerun()
        else:
            st.sidebar.error("Неверный логин или пароль")

def logout():
    if st.sidebar.button("Выйти"):
        for key in ["logged_in", "user_id", "role", "full_name"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# Отображаем блоки входа/регистрации, если пользователь не авторизован
if not st.session_state.logged_in:
    # Создаём вкладки (аккордеон) – можно переключаться
    with st.sidebar:
        tab1, tab2 = st.tabs(["🔐 Вход", "📝 Регистрация"])
        with tab1:
            login_input = st.text_input("Логин", key="login_input")
            password_input = st.text_input("Пароль", type="password", key="password_input")
            if st.button("Войти", key="login_btn"):
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("SELECT id, full_name, role FROM users WHERE login=? AND password=?", (login_input, password_input))
                user = c.fetchone()
                conn.close()
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user[0]
                    st.session_state.full_name = user[1]
                    st.session_state.role = user[2]
                    st.success(f"Добро пожаловать, {user[1]}!")
                    st.rerun()
                else:
                    st.error("Неверный логин или пароль")
        with tab2:
            new_login = st.text_input("Логин", key="reg_login")
            new_password = st.text_input("Пароль", type="password", key="reg_pass")
            new_full_name = st.text_input("ФИО", key="reg_name")
            new_role = st.selectbox("Роль", ["employee", "admin"], key="reg_role")
            if st.button("Зарегистрироваться", key="reg_btn"):
                if not new_login or not new_password or not new_full_name:
                    st.error("Заполните все поля")
                else:
                    conn = get_db_connection()
                    c = conn.cursor()
                    try:
                        c.execute("INSERT INTO users (login, password, full_name, role) VALUES (?,?,?,?)",
                                  (new_login, new_password, new_full_name, new_role))
                        conn.commit()
                        st.success(f"Пользователь {new_login} создан! Теперь войдите.")
                    except sqlite3.IntegrityError:
                        st.error("Такой логин уже существует")
                    finally:
                        conn.close()
    st.stop()  # Останавливаем выполнение, пока пользователь не войдёт

# После авторизации – показываем имя и кнопку выхода
st.sidebar.write(f"👤 **{st.session_state.full_name}** ({st.session_state.role})")
logout()

# ------------------ ФУНКЦИИ ПРИЛОЖЕНИЯ ------------------
def show_employee_panel(user_id):
    st.header("✈️ Мои командировки")
    
    with st.expander("➕ Подать новую заявку"):
        with st.form("new_trip"):
            col1, col2 = st.columns(2)
            with col1:
                city = st.text_input("Город")
                start_date = st.date_input("Дата начала")
                planned_costs = st.number_input("Планируемые расходы (руб.)", min_value=0.0, step=500.0)
            with col2:
                purpose = st.text_area("Цель командировки")
                end_date = st.date_input("Дата окончания")
            submitted = st.form_submit_button("Отправить заявку")
            if submitted and city and purpose:
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('''INSERT INTO trips (user_id, city, start_date, end_date, purpose, planned_costs, status, created_at)
                             VALUES (?,?,?,?,?,?,?,?)''',
                          (user_id, city, str(start_date), str(end_date), purpose, planned_costs, "На рассмотрении", str(datetime.now())))
                conn.commit()
                conn.close()
                st.success("Заявка отправлена!")
                st.rerun()
    
    conn = get_db_connection()
    df = pd.read_sql_query('''SELECT id, city, start_date, end_date, purpose, planned_costs, status, report_file
                              FROM trips WHERE user_id=? ORDER BY created_at DESC''', conn, params=(user_id,))
    conn.close()
    if not df.empty:
        df = df.fillna("")
        st.dataframe(df, use_container_width=True)
        
        for idx, row in df.iterrows():
            if row['status'] == 'Согласовано' and not row['report_file']:
                with st.expander(f"📎 Загрузить отчёт по командировке №{row['id']} ({row['city']})"):
                    uploaded_file = st.file_uploader("Выберите файл (txt/pdf)", type=["txt", "pdf"], key=f"upload_{row['id']}")
                    if uploaded_file and st.button("Загрузить", key=f"btn_{row['id']}"):
                        os.makedirs("reports", exist_ok=True)
                        file_path = f"reports/trip_{row['id']}_{uploaded_file.name}"
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        conn = get_db_connection()
                        c = conn.cursor()
                        c.execute("UPDATE trips SET report_file=? WHERE id=?", (file_path, row['id']))
                        conn.commit()
                        conn.close()
                        st.success("Отчёт загружен!")
                        st.rerun()
    else:
        st.info("У вас пока нет командировок.")

def show_admin_panel():
    st.header("📊 Все заявки на командировки")
    conn = get_db_connection()
    df = pd.read_sql_query('''SELECT trips.id, users.full_name, trips.city, trips.start_date, trips.end_date,
                                     trips.purpose, trips.planned_costs, trips.status, trips.report_file
                              FROM trips JOIN users ON trips.user_id = users.id
                              ORDER BY trips.created_at DESC''', conn)
    conn.close()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        
        st.subheader("✏️ Изменить статус заявки")
        trip_id = st.number_input("ID заявки", min_value=1, step=1)
        new_status = st.selectbox("Новый статус", ["Согласовано", "Отклонено", "На рассмотрении"])
        if st.button("Обновить статус"):
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("UPDATE trips SET status=? WHERE id=?", (new_status, trip_id))
            conn.commit()
            conn.close()
            st.success("Статус обновлён")
            st.rerun()
        
        if st.button("📥 Экспорт всех заявок в CSV"):
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Скачать CSV", csv, "trips_report.csv", "text/csv")
    else:
        st.info("Нет ни одной заявки.")

# ------------------ МАРШРУТИЗАЦИЯ ПО РОЛЯМ ------------------
if st.session_state.role == "admin":
    show_admin_panel()
    if st.checkbox("Посмотреть интерфейс сотрудника"):
        show_employee_panel(st.session_state.user_id)
else:
    show_employee_panel(st.session_state.user_id)