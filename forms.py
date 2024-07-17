from wtforms import StringField, SelectField, SubmitField, IntegerField, URLField, EmailField, PasswordField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Length



class AddProduct(FlaskForm):
    description = StringField('Description', validators=[DataRequired()], render_kw={'class': 'w-25 custom-label'})
    price = IntegerField('Price', validators=[DataRequired()], render_kw={'class': 'w-25 custom-label'})
    img_url = URLField('Image URL', validators=[DataRequired()], render_kw={'class': 'w-25 custom-label'})
    submit = SubmitField('Add')

class Register(FlaskForm):
    email = EmailField('Email Address', validators=[DataRequired()], render_kw={'class': 'w-25 custom-label'})
    username = StringField('Username', validators=[DataRequired()], render_kw={'class': 'w-25 custom-label'})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={'class': 'w-25 custom-label'})
    submit = SubmitField('Register',render_kw={'class': 'btn btn-light'})

class Login(FlaskForm):
    email = EmailField('Email Address', validators=[DataRequired()], render_kw={'class': 'w-25 custom-label'})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={'class': 'w-25 custom-label'})
    submit = SubmitField('Login',render_kw={'class': 'btn btn-light'})