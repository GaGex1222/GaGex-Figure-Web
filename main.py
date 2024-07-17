from datetime import date
from flask import Flask, abort, render_template, redirect, url_for, flash, request, session
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey, text
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from flask_gravatar import Gravatar
from dotenv import load_dotenv
from forms import AddProduct, Register, Login
import os
import random
from flask_mail import Mail, Message

load_dotenv()
login_manager = LoginManager()
app = Flask(__name__)
login_manager.init_app(app=app)
sql_url = os.getenv('SQL_URL')
SECRET_KEY = os.getenv('SECRET_KEY')
bootstrap = Bootstrap5(app=app)
class Base(DeclarativeBase):
  pass
db = SQLAlchemy(model_class=Base)
app.config['SECRET_KEY'] = SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = sql_url
db.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    password: Mapped[str] = mapped_column(String)
    carts = db.relationship('ShoppingCart', backref='cart_owner')

class Products(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(String)
    price: Mapped[int] = mapped_column(Integer)
    image_url: Mapped[str]
    carts = db.relationship('ShoppingCart', backref='cart_item')

class ShoppingCart(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    item: Mapped[str] = mapped_column(String)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'), nullable=False)
    item_id: Mapped[int] = mapped_column(ForeignKey('products.id'), nullable=False)


with app.app_context():
    db.create_all()
@app.route('/')
def home():
    return render_template('home.html', current_user=current_user)


    



@app.route('/add-product', methods=['POST', 'GET'])
def add_product():
    form = AddProduct()
    if form.validate_on_submit():
        with app.app_context():
            desc = request.form.get('description')
            price = request.form.get('price')
            img_url = request.form.get('img_url')
            new_product = Products(description=desc, price=price, image_url=img_url)
            db.session.add(new_product)
            db.session.commit()
        return redirect(url_for('add_product'))
    return render_template('addproduct.html', form=form)

@app.route('/register', methods=['POST', 'GET'])
def register():
    form = Register()
    if form.validate_on_submit():
        try:
            username = request.form.get('username')
            email = request.form.get("email")
            password = request.form.get('password')
            password_hashed = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
            new_user = User(
                username=username,
                email=email,
                password=password_hashed
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return render_template('home.html', current_user=current_user)
        except IntegrityError:
            flash("Email Or username is already in use, please try to use different one")
            return redirect(url_for('register'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['POST', 'GET'])
def login():
    form = Login()
    if current_user.is_authenticated:
        flash('Already Logged In')
        return redirect(url_for('home'))
    if form.validate_on_submit():
        password = request.form.get('password')
        email = request.form.get('email')
        user_trying_to_be_accessed = db.session.execute(db.select(User).where(User.email == email)).scalar()
        print(user_trying_to_be_accessed)
        if check_password_hash(user_trying_to_be_accessed.password, password):
            login_user(user_trying_to_be_accessed)
            flash('You Have Logged in successfully!')
            return redirect(url_for('home'))
        else:
            flash('Password Is Incorrect')
            return redirect(url_for('login'))
        
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    if current_user.is_authenticated:
        flash(f'{current_user.username}, You have been logged out')
        logout_user()
        return render_template('home.html')
    return render_template('home.html')

@app.route('/products', methods=['POST', 'GET'])
def products():
    with app.app_context():
        result = db.session.execute(db.select(Products)).fetchall()
    

    if request.method == 'POST':
        items = []
        search_results = request.form.get('search')
        with app.app_context():
            result = db.session.execute(db.select(Products)).fetchall()
        for item in result:
            item = item[0]
            if search_results.lower() in item.description.lower():
                items.append(item)
        return render_template('productsearch.html', items=items, search=search_results, current_user=current_user)
    return render_template("products.html", items=result, current_user=current_user)

@app.route('/delete-product', methods=['POST', 'GET'])
def delete_product():
    product_id = request.args.get('product_id')
    product_to_remove = db.session.execute(db.select(Products).where(Products.id == product_id)).scalar()
    shopping_cart_items_to_remove = db.session.execute(db.select(ShoppingCart).where(ShoppingCart.item_id == product_id)).fetchall()
    for item in shopping_cart_items_to_remove:
        item = item[0]
        db.session.delete(item)
        db.session.commit()
    db.session.delete(product_to_remove)
    db.session.commit()
    flash(f'{product_to_remove.description} Has Been removed')
    return redirect(url_for('products'))

@app.route('/cart', methods=['POST', 'GET'])
def cart():
    user_id = request.args.get('user_id')
    product_id = request.args.get('product_id')
    if not user_id == None:
        if len(user_id) == 0:
            flash("You have to log in to have a Shopping cart!")
            return redirect(url_for('products'))
        else:
            product_selcted = db.session.execute(db.select(Products).where(Products.id == product_id)).scalar()
            new_cart_item = ShoppingCart(item=product_selcted.description, user_id=user_id, item_id=product_id)
            db.session.add(new_cart_item)
            db.session.commit()
            return redirect(url_for('cart'))
    else:
        if current_user.is_authenticated:
            user_cart_items = db.session.execute(db.select(ShoppingCart).where(ShoppingCart.user_id == current_user.id)).fetchall()
            cart_items = []
            for item in user_cart_items:
                item = item[0]
                item_object = db.session.execute(db.select(Products).where(Products.id == item.item_id)).scalar()
                cart_items.append(item_object)
            total_price = 0
            for item in cart_items:
                total_price += item.price
            print(cart_items)
            return render_template('cart.html', items=cart_items, total_price=total_price)
        else:
            flash('You have to be logged in to use the cart')
            return redirect(url_for('home'))


@app.route('/delete-cart-item', methods=['POST', 'GET'])
def delete_cart_item():
    item_id = request.args.get('item_id')
    items_to_delete = db.session.execute(db.select(ShoppingCart).where((ShoppingCart.item_id == item_id) & (ShoppingCart.user_id == current_user.id))).fetchall()
    for item in items_to_delete:
        item = item[0]
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for('cart'))


@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)




