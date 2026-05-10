from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

class RegisterForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired(), Length(min=3)])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=3)])
    submit = SubmitField('Зарегистрироваться')

class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class TopicForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired()])
    submit = SubmitField('Создать тему')

class PostForm(FlaskForm):
    content = TextAreaField('Текст поста', validators=[DataRequired()])
    submit = SubmitField('Отправить')