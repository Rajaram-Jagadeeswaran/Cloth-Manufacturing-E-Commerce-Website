from functools import wraps
from flask import Flask, redirect, render_template, request, url_for, session, flash, jsonify
from flask_cors import CORS, cross_origin
from flask_wtf import CSRFProtect
import requests, secrets
import re
from flask_wtf import FlaskForm
from sqlalchemy.exc import IntegrityError
from wtforms import BooleanField, IntegerField, StringField, PasswordField, SubmitField, ValidationError
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
import uuid
import base64
from  lib.rjag22239243Discount.discount import OrderCheckoutProcessor

application = Flask(__name__, static_url_path='/static')
application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
application.debug = True
application.config['SECRET_KEY'] = secrets.token_urlsafe(16) 
csrf = CSRFProtect(application)
CORS(application)

APIGATEWAY_ENDPOINT = 'https://0a56p4zzr4.execute-api.sa-east-1.amazonaws.com/stage1'
COUPON_API = 'https://qjc1v6hvs1.execute-api.sa-east-1.amazonaws.com/X22239243_CouponCodes'
REVIEW_API = "https://2arbn3zs3e.execute-api.eu-west-1.amazonaws.com/dev"

db = SQLAlchemy(application)
migrate = Migrate(application, db)
user_cart = []
order_processor = OrderCheckoutProcessor()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class SignUpForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    is_admin = BooleanField('Admin')
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email.data):
            raise ValidationError('Invalid email address.')

    def validate_password(self, password):
        if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$", password.data):
            raise ValidationError('Password must be at least 8 characters long and contain at least one lowercase letter, one uppercase letter, one numeric digit, and one special character.')

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired()])
    product_discription = StringField('Product Discription', validators=[DataRequired()])
    price = StringField('Price', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    submit = SubmitField('Submit')

def is_authenticated(username, password):
    user = User.query.filter_by(username=username).first()
    return user

def login_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if 'username' in session:
            return route_function(*args, **kwargs)
        else:
            return redirect(url_for('home'))
    return wrapper

def get_user_id_from_session():
    if 'user_id' in session:
        return session['user_id']
    else:
        return None
    
def get_user_id_from_database():
    if 'username' in session:
        username = session['username']
        user = User.query.filter_by(username=username).first()
        if user:
            return user.id  
    return None  

def get_email_from_database():
    if 'username' in session:
        username = session['username']
        user = User.query.filter_by(username=username).first()
        if user:
            return user.email
    return None  

@application.route('/')
def home():
    return render_template('home.html')
    # A-Max web home page route

@application.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        is_admin = form.is_admin.data
        # A-Max web signup page route with user, email and password validations
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please use a different username.', 'danger')
            return redirect(url_for('signup'))

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Invalid email address.', 'danger')
            return redirect(url_for('signup'))

        if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$", password):
            flash('Password must be at least 8 characters long and contain at least one lowercase letter, one uppercase letter, one numeric digit, and one special character.', 'danger')
            return redirect(url_for('signup'))

        try:
            new_user = User(username=username, email=email, password=password, is_admin=is_admin)
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully. Please log in.', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()  # Rollback the transaction in case of IntegrityError
            flash('Email address is already in use. Please use a different email address.', 'danger')
            return redirect(url_for('signup'))

    return render_template('signup.html', form=form)

@application.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if request.method == 'POST' and form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username, password=password).first()

        try:
            # A-Max web login page route with user autendication
            if user:
                session['username'] = username
                session['user_id'] = user.id
                session['admin'] = user.is_admin
                if user.is_admin:
                    return redirect('/product')
                else:
                    return redirect('/catalogue')
            else:
                flash('Login unsuccessful. Please check username and password.', 'danger')
        except IntegrityError:
            flash('An error occurred while processing your request. Please try again.', 'danger')

    return render_template('login.html', form=form)

@application.route('/logout')
@login_required
def logout():
    session.pop('username', None)
    return render_template('logout.html')

@application.route('/catalogue', methods=['GET', 'POST'])
@login_required
@csrf.exempt
def catalogue():
    # A-Max web catalogue route for users shopping landing page
    response = requests.post(f'{APIGATEWAY_ENDPOINT}', json={'operation': 'get_all_products'})
    data = response.json()
    return render_template('product_listing.html', Products=data)
 
@application.route('/product', methods=['GET'])
@login_required
@csrf.exempt
def display_products():
    try:
        # A-Max web catalogue route for users shopping landing page
        response = requests.post(f'{APIGATEWAY_ENDPOINT}', json={'operation': 'get_all_products'})
        data = response.json()
        response.raise_for_status()
        return render_template('index.html', Products=data)
    except Exception as e:
        return f"Error: {str(e)}"

@application.route('/orders', methods=['GET'])
@login_required  
def view_orders():
    try:
        # A-Max web order route for order details admin can view
        response = requests.post(f'{APIGATEWAY_ENDPOINT}', json={'operation': 'get_order_details'})
        orders = response.json()
        response.raise_for_status()
        return render_template('orders.html', order_details=orders)

    except Exception as e:
        flash(f"Error retrieving orders: {str(e)}", 'danger')
        return render_template('error.html', error=f"Error retrieving orders: {str(e)}")
    
@application.route('/coupon', methods=['GET', 'POST'])
@login_required  
@cross_origin()
@csrf.exempt
def coupon():
    try:
        response = requests.post(f'{COUPON_API}', json={'operation': 'get_coupon_details'})
        coupons = response.json()
        response.raise_for_status()
        return render_template('coupon.html', coupon_details=coupons)

    except Exception as e:
        flash(f"Error retrieving coupons: {str(e)}", 'danger')
        return render_template('error.html', error=f"Error retrieving coupons: {str(e)}")

@application.route('/generate_coupon', methods=['POST'])
@login_required
@csrf.exempt
def generate_coupon():
    try:
        # Call the create_coupon_code operation
        response = requests.post(COUPON_API, json={'operation': 'create_coupon_code'})
        response.raise_for_status()
        data = response.json()
        print(data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@application.route('/apply_coupon', methods=['GET','POST'])
@login_required
@csrf.exempt
def apply_coupon():
    try:
        coupon_code = request.form.get('coupon_code')
        order_total = request.form.get('order_total')
        response = requests.post(COUPON_API, json={'operation': 'validate_coupon', 'coupon_code': coupon_code, 'order_total': order_total })
        data = response.json()
        print(coupon_code)
        print(order_total)
        print(data)
        response.raise_for_status()
        if response.status_code == 200:
            # Extract discount and new total from the response
            discount = data.get('discount')
            new_total = data.get('new_total')
            if discount is None and new_total is None:
                return jsonify({'success': False, 'message': 'Invalid coupon'})
            else:
                return jsonify({'success': True, 'discount': discount, 'new_total': new_total})
        else:
            return jsonify({'success': False, 'message': 'Error applying coupon'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    
@application.route('/product_reviews', methods=['GET', 'POST'])
@login_required
@cross_origin()
@csrf.exempt
def product_reviews():
    if request.method == 'GET':
        # Get reviews for a specific product
        rid = request.args.get('rid')
        application = 'A=Max'
        user_id = get_user_id_from_database()  # Assuming this function retrieves the user_id
        reviews = get_reviews_from_api(rid, application, user_id)
        return jsonify(reviews)
    elif request.method == 'POST':
        # Submit a new review
        data = request.json
        response = submit_review_to_api(data)
        if response.status_code == 201:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': response.text})

def get_reviews_from_api(rid, application, user_id):
    response = requests.get(REVIEW_API, params={'rid': rid, 'application': application, 'user_id': user_id})
    if response.status_code == 200:
        return response.json()
    else:
        return []

def submit_review_to_api(data):
    response = requests.post(REVIEW_API, json=data)
    return response

@application.route('/add_product', methods=['GET', 'POST'])
@login_required
@cross_origin()
@csrf.exempt
def add_product():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            product_discription = request.form.get('product_discription')
            price = request.form.get('price')
            quantity = request.form.get('quantity')

            image = request.files.get('image')
            
            if image:
                image_data = image.read()
                image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            payload = {
                'operation': 'add_product',
                'name': name,
                'product_discription': product_discription,
                'price': price,
                'quantity': quantity,
                'image_base64': image_base64
            }
            response = requests.post(APIGATEWAY_ENDPOINT, json=payload)
            data = response.json()
            if response.status_code == 200:
                return redirect(url_for('display_products'))  
            else:
                error_message = f"Received status code {response.status_code} from the API"
                return render_template('error.html', error=error_message)

        except KeyError as e:
            error_message = f"Key not found in request form: {str(e)}"
            return render_template('error.html', error=error_message)

        except requests.RequestException as e:
            error_message = f"Request Exception: {str(e)}"
            return render_template('error.html', error=error_message)

        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_template('error.html', error=error_message)

    return render_template('products.html')

@application.route('/add_to_cart', methods=['POST'])
@login_required
@csrf.exempt
def add_to_cart():
    try:
        # A-Max web add_to_cart route handles the user's shopping cart specifications
        productId = request.form.get('productId')
        product_name = request.form.get('name')
        product_price = request.form.get('price')
        product_quantity = int(request.form.get('quantity'))

        cart_item = {
            "productId": productId,
            "name": product_name,
            "price": product_price,
            "quantity": product_quantity
        }
        user_id = get_user_id_from_database()
        cart_item_id = str(uuid.uuid4())
        payload = {
            "operation": 'add_to_cart',
            "user_id": user_id,
            "cart_item": cart_item,
            "cart_item_id": cart_item_id
        }
        user_cart.append(cart_item)
        response = requests.post(APIGATEWAY_ENDPOINT, json=payload)
        data = response.json()
        flash('Product added to cart successfully.', 'success')  

    except Exception as e:
        flash(f"Error adding product to cart: {str(e)}", 'danger')  

    return redirect(request.referrer)

@application.route('/cart', methods=['GET'])
@login_required
def cart():
    try:
        # A-Max web cart route handles user's cart items 
        user_id = get_user_id_from_database()

        if user_id is not None:
            payload = {
                "operation": 'get_user_cart',
                "user_id": user_id
            }
            response = requests.post(APIGATEWAY_ENDPOINT, json=payload)
            cart_item = response.json()

            if response.status_code == 200:
                total_price = sum(float(item['cart_item']['price']) * int(item['cart_item']['quantity']) for item in cart_item)
                print(total_price)
                return render_template('cart.html', cart_items=cart_item, total=total_price)
            else:
                error_message = f"Received status code {response.status_code} from the API"
                return render_template('error.html', error=error_message)

        else:
            flash('User not found. Please log in again.', 'danger')
            return redirect(url_for('login'))

    except Exception as e:
        flash(f"Error retrieving cart items: {str(e)}", 'danger')
        return redirect(request.referrer)
    
@application.route('/get_location_address', methods=['GET', 'POST'])
@login_required
@csrf.exempt
def get_location_address():
    try:
        # Get latitude and longitude from the request
        latitude = float(request.form.get('latitude'))
        longitude = float(request.form.get('longitude'))
        print(latitude)
        print(longitude)

        # Make request to OpenStreetMap Nominatim API
        response = requests.get(f'https://nominatim.openstreetmap.org/reverse?lat={latitude}&lon={longitude}&format=json')
        data = response.json()

        # Extract address information from the response
        address = data.get('display_name')
        print(address)

        return jsonify({'success': True, 'address': address})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    
@application.route('/remove_from_cart', methods=['POST'])
@login_required
@csrf.exempt
def remove_from_cart():
    try:
        # A-Max web remove_from_cart route handles the user's cart items deletion
        cart_item_id = request.form.get('cart_item_id')
        user_id = get_user_id_from_database()
        print("Inside remove_from_cart_route")
        print("userd_id:",user_id)

        print("In here")

        response = requests.post(
            APIGATEWAY_ENDPOINT,
            json={'operation': 'remove_from_cart', 'cart_item_id': cart_item_id}
        )
        flash('Item removed from cart successfully.', 'success')
        
        print('response',response)

        response.raise_for_status()
        return redirect('/cart')

    except Exception as e:
        flash(f"Error removing item from cart: {str(e)}", 'danger')
        return render_template('error.html', error=f"Error viewing cart: {str(e)}")

@application.route('/place_order', methods=['GET', 'POST'])
@login_required
@csrf.exempt
def place_order():
    try:
        # A-Max web place_order route handles place order functionlities
        user_id = get_user_id_from_database()
        email= get_email_from_database()
        delivery_address= request.form.get('delivery_address')
        payload = {
                "operation": 'get_user_cart',
                "user_id": user_id
            }
        response = requests.post(APIGATEWAY_ENDPOINT, json=payload)
        cart_items = response.json()
        print("items: ", cart_items)
        print("email: ", email)

        checkout_price = float(request.form.get('checkout_price'))
        print(checkout_price)

        order_id = str(uuid.uuid4())
        cart_item_ids = [item['cart_item_id'] for item in cart_items]

        # Discount calculation
        discount_price = order_processor.create_order(checkout_price, discount=0.1)
        print("Discounted_price:", discount_price)

        # Tax calculation for the order
        overall_tax = order_processor.calculate_tax(discount_price)
        tax = round(overall_tax, 2)
        print("Tax:", tax)

        # Shipping cost calculation for the order
        shipping_cost = order_processor.calculate_shipping(discount_price)

        net_total = order_processor.calculate_net_total(discount_price)
        print("Shipping Cost:", shipping_cost)
        print("NET Total:", net_total)

        payload = {
                "operation": 'create_order',
                "order_id": order_id,
                "user_id": user_id,
                "cart_item": cart_items,
                "cart_item_id": cart_item_ids,
                "checkout_price": checkout_price,
                "delivery_address": delivery_address,
                "email": email,
                "discount_price": discount_price,
                "tax": tax,
                "shipping_cost": shipping_cost,
                "net_total": net_total
            }
        response = requests.post(APIGATEWAY_ENDPOINT, json=payload)
        data = response.json()
        print('data:',data)
        print("I'm also here")

        flash('Order placed successfully.', 'success')
        return render_template('order_placed.html', order_items=data)

    except Exception as e:
        flash(f"Error placing the order: {str(e)}", 'danger')
        return render_template('error.html', error=f"Error placing the order: {str(e)}")

 
if __name__ == "__main__":
    with application.app_context():
        db.create_all()
    application.run()