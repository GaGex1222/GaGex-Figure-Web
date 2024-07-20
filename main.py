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
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from forms import AddProduct, Register, Login, UploadFile
import os
import datetime
import random
from flask_mail import Mail, Message
import json

load_dotenv()
login_manager = LoginManager()
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'xlsx'}
app = Flask(__name__)
login_manager.init_app(app=app)
sql_url = os.getenv('SQL_URL')
SECRET_KEY = os.getenv('SECRET_KEY')
EMAIL_KEY = os.getenv('EMAIL_KEY')
bootstrap = Bootstrap5(app=app)
class Base(DeclarativeBase):
  pass
db = SQLAlchemy(model_class=Base)
app.config['SECRET_KEY'] = SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = sql_url
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'gald12123434@gmail.com'
app.config['MAIL_PASSWORD'] = EMAIL_KEY
mail = Mail(app)
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

class Order(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(Integer)
    user_id: Mapped[int] = mapped_column(Integer)
    items: Mapped[str] = mapped_column(String)
    full_name: Mapped[str] = mapped_column(String)
    address: Mapped[str] = mapped_column(String)
    country: Mapped[str] = mapped_column(String)
    phone_number: Mapped[str] = mapped_column(String)
    total_price: Mapped[str] = mapped_column(String)
    date: Mapped[str] = mapped_column(String)

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

def check_for_double_item_in_cart():
    all_user_items_in_cart = db.session.execute(db.select(ShoppingCart).where(ShoppingCart.user_id == current_user.id)).fetchall()
    all_item_ids_in_cart = []
    for cart in all_user_items_in_cart:
        cart = cart[0]
        all_item_ids_in_cart.append(cart.item_id)
    return all_item_ids_in_cart

def retrieve_items_from_order_table(order):
    items_ordered = order.items.split(',')
    items_ordered_db_objects = []
    for item in items_ordered:
        item_ordered_db_object = db.session.execute(db.select(Products).where(Products.id == item)).scalar()
        items_ordered_db_objects.append(item_ordered_db_object)
    items_descs = []
    for item in items_ordered_db_objects:
        items_descs.append(item.description)
    items_names_cleared = ', '.join(items_descs)
    return items_names_cleared


def check_valid_file(filename):
    if not '.' in filename:
        return False
    else:
        fileename_ext = filename.split('.')[1]
        if fileename_ext == 'txt':
            return True

with app.app_context():
    db.create_all()
    all_prods = []
    all_prod = db.session.execute(db.select(Products)).fetchall()
    for prod in all_prod:
        prod = prod[0]
        all_prods.append(prod.description)
@app.route('/')
def home():
    return render_template('home.html', current_user=current_user)






@app.route('/add-product', methods=['POST', 'GET'])
def add_product():
    if current_user.id == 1:
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
    else:
        flash('You have to be an admin to enter this URL!')
        return redirect(url_for('home'))

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
    form = UploadFile()
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
            if form.validate_on_submit():
                file = form.file.data # Get File uploaded by user!
                if file and check_valid_file(file.filename):
                    file.save(os.path.join('static/uploads', secure_filename(file.filename)))
                    with open(os.path.join('static/uploads', file.filename), 'r') as file_of_products:
                        file_lines = file_of_products.readlines()[0]
                        products_sperated = file_lines.split(',')
                        for prod in products_sperated:
                            prod_whitespace_seperated = prod.split(' ')
                            for prod_whitespaced in prod_whitespace_seperated:
                                for p in all_prods:
                                    if prod_whitespaced.lower() in p.lower():

                                        product_to_add_to_cart = db.session.execute(db.select(Products).where(Products.description == p)).scalar()
                                        new_cart_item = ShoppingCart(
                                            item=p,
                                            user_id=current_user.id,
                                            item_id=product_to_add_to_cart.id
                                        )
                                        item_ids_in_cart = check_for_double_item_in_cart()
                                        if new_cart_item.item_id not in item_ids_in_cart:
                                            db.session.add(new_cart_item)
                                            db.session.commit()

                                        # db.session.add(new_cart_item)
                                        # db.session.commit()

                                    

                    flash("File Has Been uploaded, please wait while we check what products are matching the products in your file!")
                    return redirect(url_for('cart'))
                else:
                    print(file.filename)


                    
            

            user_cart_items = db.session.execute(db.select(ShoppingCart).where(ShoppingCart.user_id == current_user.id)).fetchall()
            cart_items = []
            for item in user_cart_items:
                item = item[0]
                item_object = db.session.execute(db.select(Products).where(Products.id == item.item_id)).scalar()
                cart_items.append(item_object)
            total_price = 0
            for item in cart_items:
                total_price += item.price
            return render_template('cart.html', form=form, items=cart_items, total_price=total_price)
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

@app.route('/checkout', methods=['POST', 'GET'])
def checkout():
    user_cart = db.session.execute(db.select(ShoppingCart).where(ShoppingCart.user_id == current_user.id)).fetchall()
    if len(user_cart) == 0:
        flash('You have to have items in cart to make a purchase!')
        return redirect(url_for('cart'))
    cleared_items = []
    for item in user_cart:
        item = item[0]
        product = db.session.execute(db.select(Products).where(Products.id == item.item_id)).scalar()
        cleared_items.append(product)
    total_price = 0
    for item in cleared_items:
        total_price += item.price
    if request.method == 'POST':
        first_name = request.form.get('firstname')
        last_name = request.form.get('lastname')
        full_name = f'{first_name} {last_name}'
        address = request.form.get('address')
        country = request.form.get('country')
        today = str(datetime.datetime.today())
        phone_number = request.form.get('phonenumber')
        user_items_ids = []
        for item in user_cart:
            item = item[0]
            user_items_ids.append(str(item.item_id))
        items_csv = ','.join(user_items_ids)
        order_num = ''
        for _ in range(10):
            order_num += str(random.randint(1, 9))
        new_order = Order(
            order_id=order_num,
            user_id=current_user.id,
            items=items_csv,
            full_name=full_name,
            address=address,
            country=country,
            phone_number=phone_number,
            total_price=total_price,
            date=today
        )
        db.session.add(new_order)
        db.session.commit()


        return redirect(url_for('order_payed', order_num=order_num))

    return render_template('checkout.html', items=cleared_items, total_price=total_price)

@app.route('/order-payed/<int:order_num>')
def order_payed(order_num):
    order = db.session.execute(db.select(Order).where(Order.order_id == order_num)).scalar()
    items_ordered = retrieve_items_from_order_table(order=order)
    msg = Message(subject='Thank you for your order!', sender='galalsops@gmail.com', recipients=[current_user.email])
    msg.body = f"Hey {current_user.username}, We are happy that you decided to order from our website!\nOrder Number: {order.order_id}\nitems: {items_ordered}\naddress for delievery : {order.address}\ncountry : {order.country}\nTotal price : {order.total_price}\ndate of order : {order.date}"
    mail.send(msg)
    user_cart = db.session.execute(db.select(ShoppingCart).where(ShoppingCart.user_id == current_user.id)).fetchall()
    
    items_objs = []
    print(items_ordered.split(','))

    for item in items_ordered.split(','):
        print(item)
        item_obj = db.session.execute(db.select(Products).where(Products.description == item.strip())).scalar()
        items_objs.append(item_obj)
    total_price = 0
    for item in items_objs:
        total_price += item.price
    for item in user_cart:
        item = item[0]
        db.session.delete(item)
        db.session.commit()
    
    return render_template('orderpayed.html', order=order, items=items_ordered, total_price=total_price)

@app.route('/check-order', methods=['POST', 'GET'])
def check_order():
    if current_user.id == 1:
        if request.method == 'POST':
            try:
                order_num = request.form.get('order_number')
                order_obj = db.session.execute(db.select(Order).where(Order.order_id == order_num)).scalar()
                items_ordered = retrieve_items_from_order_table(order=order_obj)
                return render_template('checkorderdetails.html', order=order_obj, items=items_ordered)
            except:
                flash('Order number dont exist.')
                return redirect(url_for('check_order'))
        return render_template('checkorder.html')
    else:
        flash('You have to be an admin to enter this URL!')
        return redirect(url_for('home'))

@app.route('/contact-us', methods=['POST', 'GET'])
def contact_us():
    name = request.form.get('name')
    email = request.form.get('email')
    subject = request.form.get('subject')
    order_number = request.form.get('order_number')
    message = request.form.get('message')
    if request.method == 'POST':
        msg = Message(subject=f'{request.form.get('subject')} (GaGex Figures Website!)', sender=f'{request.form.get('email')}', recipients=['gald12123434@gmail.com', 'galalsops@gmail.com'])
        msg.body = (
            f"Name: {name}\n"
            f"Email: {email}\n"
            f"Subject: {subject}\n"
            f"Order Number: {order_number}\n"
            f"Message: {message}"
        )
        mail.send(msg)
        flash("Your message has been sent successfully!")
        return redirect(url_for('contact_us'))
    return render_template('contactus.html')

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)




