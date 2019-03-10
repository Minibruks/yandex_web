from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired
from flask import Flask, redirect, render_template, request
import sqlite3


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
session = {}


class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class AddUserForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Добавить')


class AddBooksForm(FlaskForm):
    title = StringField('Название книги', validators=[DataRequired()])
    content = TextAreaField('Текст', validators=[DataRequired()])
    label = StringField('Ссылка на обложку книги', validators=[DataRequired()])
    book_count = StringField('Количество экземпляров', validators=[DataRequired()])
    submit = SubmitField('Добавить')


class DB:
    def __init__(self):
        conn = sqlite3.connect('news.db', check_same_thread=False)
        self.conn = conn

    def get_connection(self):
        return self.conn

    def __del__(self):
        self.conn.close()


class UserModel:
    def __init__(self, connection):
        self.connection = connection

    def init_table(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                             user_name VARCHAR(50),
                             password_hash VARCHAR(128)
                             )''')
        cursor.close()
        self.connection.commit()

    def insert(self, user_name, password_hash):
        cursor = self.connection.cursor()
        cursor.execute('''INSERT INTO users 
                          (user_name, password_hash) 
                          VALUES (?,?)''', (user_name, password_hash))
        cursor.close()
        self.connection.commit()

    def get(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (str(user_id)))
        row = cursor.fetchone()
        return row

    def get_all(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        return rows

    def exists(self, user_name, password_hash):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE user_name = ? AND password_hash = ?",
                       (user_name, password_hash))
        row = cursor.fetchone()
        return (True, row[0]) if row else (False,)


class Library:
    def __init__(self, connection):
        self.connection = connection

    def init_table(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS library
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                            title VARCHAR(100),
                            content VARCHAR(1000),
                            label VARCHAR(1000)
                            )''')
        cursor.close()
        self.connection.commit()

    def insert(self, title, content, label, book_count):
        cursor = self.connection.cursor()
        cursor.execute('''INSERT INTO library 
                                  (title, content, label, count) 
                                  VALUES (?,?,?,?)''', (title, content, label, str(book_count)))
        cursor.close()
        self.connection.commit()

    def get(self, title):
        cursor = self.connection.cursor()
        cursor.execute("SELECT title, content, label, id, count FROM library WHERE title = ?", title)
        row = cursor.fetchone()
        return row

    def get_all(self, view_all=True):
        cursor = self.connection.cursor()
        if view_all:
            cursor.execute("SELECT title, content, label, id, count FROM library ORDER BY title")
        else:
            cursor.execute("SELECT title, content, label, id, count FROM library WHERE count > 0  ORDER BY title")
        rows = cursor.fetchall()
        return rows


class Books:
    def __init__(self, connection):
        self.connection = connection

    def init_table(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS books 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                             library_id INTEGER,
                             user_id INTEGER
                             )''')
        cursor.close()
        self.connection.commit()

    def insert(self, library_id, user_id):
        cursor = self.connection.cursor()
        cursor.execute('''INSERT INTO books 
                          (library_id, user_id) 
                          VALUES (?,?)''', (str(library_id), str(user_id)))
        cursor.execute('''UPDATE library SET count = count - 1 WHERE id = ?''', str(library_id))
        cursor.close()
        self.connection.commit()

    def get(self, book_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM books WHERE id = ?", (str(book_id)))
        row = cursor.fetchone()
        return row

    def get_all(self, book_id=None):
        cursor = self.connection.cursor()
        if book_id:
            cursor.execute('''SELECT library.title, library.content, library.label, books.id FROM books 
                            LEFT JOIN library ON books.library_id = library.id  
                            WHERE user_id = ? ORDER BY library.title''',
                           (str(book_id)))
        else:
            cursor.execute("SELECT * FROM books")
        rows = cursor.fetchall()
        return rows

    def delete(self, book_id):
        cursor = self.connection.cursor()
        cursor.execute('''DELETE FROM books WHERE id = ?''', (str(book_id)))
        cursor.close()
        self.connection.commit()

    def remove(self, book_id):
        cursor = self.connection.cursor()
        cursor.execute('''SELECT library_id FROM books WHERE id = ? ''', (str(book_id)))
        rows = cursor.fetchone()
        cursor.execute('''UPDATE library SET count = count + 1 WHERE id = ?''', str(rows[0]))
        self.delete(book_id)
        cursor.close()
        self.connection.commit()


db = DB()
connect = db.get_connection()
users = UserModel(connect)
users.init_table()

books = Books(connect)
books.init_table()

library = Library(connect)
library.init_table()

# books.insert('Война и мир', 'Пока пусто', '3')
# users.insert('Pavel', '1234')
# print(users.get_all())
# print(books.get_all())
# print(library.get_all())


@app.route('/admin')
def admin():
    # all_users = list('</td><td>'.join(list(map(str, [elem[0], elem[1], ' пароль', elem[2]]))) for elem in users.get_all())
    all_users = list(users.get_all())
    users_list = []
    for row_u in all_users:
        row = []
        for el in row_u:
            row.append(el)
        row.append(str(len(books.get_all(row_u[0]))))
        users_list.append(row)
        # all_users[i].append(str(len(books.get_all(users.get_all()[i][0]))))
    # print(users_list)
    return render_template('admin.html', users=users_list)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    flag = True
    if request.method == 'GET':
        return render_template('login.html', title='Авторизация', form=form, success=flag)
    elif request.method == 'POST':
        user_name = form.username.data
        password = form.password.data
        exists = users.exists(user_name, password)
        if exists[0]:
            session['username'] = user_name
            session['user_id'] = exists[1]
            return redirect('/index')
        else:
            return render_template('login.html', title='Авторизация', form=form, success=False)


@app.route('/admin_add_user', methods=['GET', 'POST'])
def admin_add_user():
    form = AddUserForm()
    if form.validate_on_submit():
        users.insert(form.username.data, form.password.data)
        return redirect('/admin')
    return render_template('admin_add_user.html', title='Добавление пользователя', form=form)


@app.route('/admin_book_list')
def admin_book_list():
    all_books = list((elem[0], elem[2], elem[4]) for elem in library.get_all())
    return render_template('admin_book_list.html', book_list=all_books)


@app.route('/')
@app.route('/index')
def index():
    if 'username' not in session:
        return redirect('/login')
    all_books = books.get_all(session['user_id'])
    return render_template('index.html', session=session,
                           book_list=all_books)


@app.route('/admin_add_book', methods=['GET', 'POST'])
def admin_add_book():
    form = AddBooksForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        label = form.label.data
        book_count = form.book_count.data
        library.insert(title, content, label, book_count)
        return redirect('/admin_book_list')
    return render_template('admin_add_book.html', form=form, title='Добавление книги')


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if 'username' not in session:
        return redirect('/login')
    all_books = list((elem[0], elem[2], elem[3]) for elem in library.get_all(False))
    return render_template('user_add_book.html', book_list=all_books, title='Добавление книги')


@app.route('/add_book_act/<lib_id>')
def add_book_act(lib_id):
    books.insert(lib_id, session['user_id'])
    return redirect('/index')


@app.route('/remove_book/<books_id>')
def remove_book(books_id):
    books.remove(books_id)
    return redirect('/index')


@app.route('/logout')
def logout():
    session.pop('username', 0)
    session.pop('user_id', 0)
    return redirect('/login')


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')