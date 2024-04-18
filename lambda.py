import boto3
import json
from decimal import Decimal
import uuid
import base64
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource('dynamodb', region_name='sa-east-1')
products_table_name = 'x22239243_Products'  
orders_table_name = 'x22239243_orders'  
cart_table_name = 'x22239243_cart'

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        return super(DecimalEncoder, self).default(o)

def get_all_products():
    table = dynamodb.Table(products_table_name)
    response = table.scan()
    products = response['Items']
    return products

def get_order_details():
    table = dynamodb.Table(orders_table_name)

    try:
        response = table.scan()
        order_details = response['Items']
        return order_details
        print(order_details)

    except Exception as e:
        print(f'Error getting order details: {str(e)}')
        raise Exception(f'Error getting order details: {str(e)}')

def upload_image_to_s3(image_data, product_id):
    s3_bucket_name = 'x22239243-cpp-project-bucket'
    s3_object_key = f'x22239243/{product_id}.png'

    s3 = boto3.client('s3', region_name='sa-east-1')

    try:
        image_binary_data = base64.b64decode(image_data)
        
        s3.put_object(Body=image_binary_data, Bucket=s3_bucket_name, Key=s3_object_key)
        
        s3_url = f'https://{s3_bucket_name}.s3.amazonaws.com/{s3_object_key}'
        return s3_url
    except ClientError as e:
        print(f'Error uploading image to S3: {str(e)}')
        raise Exception(f'Error uploading image to S3: {str(e)}') 
    
def create_order(order_id, user_id, cart_item, cart_item_id, delivery_address, checkout_price, email, discount_price, tax, shipping_cost, net_total):
    table = dynamodb.Table(orders_table_name)
    cart_table = dynamodb.Table(cart_table_name)
    print("Inside order")
    checkout_price = 0 if checkout_price is None else checkout_price
    discount_price = 0 if discount_price is None else discount_price
    tax = 0 if tax is None else tax
    net_total = 0 if net_total is None else net_total
    
    checkout_price_decimal = Decimal(str(checkout_price))
    discount_price_decimal = Decimal(str(discount_price))
    tax_decimal = Decimal(str(tax))
    net_total_decimal = Decimal(str(net_total))
    
    try:
        table.put_item(
            Item={
                'order_id': order_id,
                'user_id': user_id,
                'cart_items': cart_item,
                'cart_item_id': cart_item_id,
                'checkout_price': checkout_price_decimal,
                'delivery_address': delivery_address,
                'email': email,
                'discount_price': discount_price_decimal,
                'tax': tax_decimal,
                'shipping_cost': shipping_cost,
                'net_total': net_total_decimal
            }
        )
        print("Order created successfully.")
        gsi_index_name = 'user_id-index'
        response = table.scan(FilterExpression=Attr('order_id').eq(order_id))
        items = response.get('Items', [])
        
        order_list = []

        for order in items:
            order_details = {
                'order_id': order.get('order_id'),
                'user_id': order.get('user_id'),
                'delivery_address': order.get('delivery_address'),
                'checkout_price': order.get('checkout_price'),
                'email': order.get('email'),
                'cart_items': [],
                'discount_price': order.get('discount_price'),
                'tax': order.get('tax'),
                'shipping_cost': order.get('shipping_cost'),
                'net_total': order.get('net_total')
            }
            
            print("order:",order)
            
            for cart_item in order.get('cart_items', []):
                cart_item_details = {
                    'item': {
                        'quantity': cart_item.get('cart_item', {}).get('quantity'),
                        'name': cart_item.get('cart_item', {}).get('name'),
                        'price': cart_item.get('cart_item', {}).get('price'),
                        'product_id': cart_item.get('cart_item', {}).get('product_id'),
                    }
                }

                order_details['cart_items'].append(cart_item_details)

            order_list.append(order_details)

        print("Orders Retrieved:", order_list)
        
        for item_id in cart_item_id:
            # Delete each item
            cart_table.delete_item(
                Key={'cart_item_id': item_id}
            )

        return order_list
    except ClientError as e:
        print(f'Error creating order: {str(e)}')
        raise Exception(f'Error creating order: {str(e)}')
        
def update_orders(order_id, product_id, quantity):
    table = dynamodb.Table(orders_table_name)
    response = table.update_item(
        Key={
            'order_id': order_id
        },
        UpdateExpression='SET product_id = :pid, quantity = :qty',
        ExpressionAttributeValues={
            ':pid': product_id,
            ':qty': quantity
        }
    )
def add_to_cart(cart_item_id, cart_item, user_id):
    table = dynamodb.Table(cart_table_name)
    print("Inside cart")
    try:
        response = table.put_item(
            Item={
                'cart_item_id': cart_item_id,  # Generate a unique cart ID
                'cart_item': cart_item,
                'user_id': user_id
            }
        )
        print("Item added to the cart successfully.")
    
        return {'message': 'Item added to the cart successfully.'}
    except ClientError as e:
        print(f'Error adding item to the cart: {str(e)}')
        raise Exception(f'Error adding item to the cart: {str(e)}')
    
def add_product(name, product_discription, price, quantity, image_data):
    table = dynamodb.Table(products_table_name)
    response = table.scan()
    products = response['Items']
    product_id = len(products) + 1
    
    s3_url = upload_image_to_s3(image_data, product_id)
    
    response= table.put_item(
        Item={
            'product_id': product_id,
            'product_discription': product_discription,
            'name': name,
            'price': Decimal(price),
            'quantity': quantity,
            'image_url': s3_url
        }
    )
    
def get_user_cart(user_id):
    table = dynamodb.Table(cart_table_name)
    print("Inside get_user_cart. User ID:", user_id)
    try:
        response = table.scan(FilterExpression=Attr('user_id').eq(user_id))
        user_cart = response['Items']
        print("User cart retrieved successfully:", user_cart)
        return user_cart
    except Exception as e:
        print("Error in get_user_cart:", str(e))
        raise e

def remove_from_cart(cart_item_id):
    table = dynamodb.Table(cart_table_name)
    try:
        print("Executing remove_from_cart function...")
        table.delete_item(Key={'cart_item_id': cart_item_id})
        
        print("Item removed from the cart successfully.")
        return {'message': 'Item removed from the cart successfully.'}
        
    except ClientError as e:
        print(f'Error removing item from the cart: {str(e)}')
        raise Exception(f'Error removing item from the cart: {str(e)}')
        
def send_email_notification(order_id, email_address):
    sns = boto3.client('sns', region_name='sa-east-1') 
    topic_arn = 'arn:aws:sns:sa-east-1:250738637992:x22239243_a-max_mailing_system' 

    message = f"Your order with reference #{order_id} has been placed successfully. Thank you for shopping with us!"

    try:
        response = sns.publish(
            TopicArn=topic_arn,
            Message=message,
            Subject="Order Placed Notification",
            MessageAttributes={
                'email': {
                    'DataType': 'String',
                    'StringValue': email_address
                }
            }
        )
        print(response)
    except ClientError as e:
        print(f'Error sending email notification: {str(e)}')
        
def lambda_handler(event, context):
    try:
        from boto3.dynamodb.conditions import Attr
        
        event_body = json.loads(event['body'])
        print('event_body =',event_body)
        operation = event_body.get('operation')
        print('operation =',operation)
        print('event =',event)
        if 'operation' in event_body:
            print("INside event_body if")
            # operation = event.body['operation']
            if operation == 'update_order':  # Update Orders table
                order_id = event['order_id']
                product_id = event['product_id']
                quantity = event['quantity']
                update_orders(order_id, product_id, quantity)
                return {
                    'statusCode': 200,
                    'body': json.dumps('Order updated successfully', cls=DecimalEncoder),
                    'headers': {"Content-Type": "application/json"}
                }
            elif operation == 'add_product':  # Add a product to Products table
                # product_id = event['product_id']
                name = event_body.get('name')
                product_discription = event_body.get('product_discription')
                price = float(event_body.get('price'))
                quantity = event_body.get('quantity')
                image_data = event_body.get('image_base64')
                add_product(name, product_discription, price, quantity,image_data)
                return {
                    'statusCode': 200,
                    'body': json.dumps('Product added successfully', cls=DecimalEncoder)
                }
            elif operation == 'add_to_cart':
                cart_item_id = event_body.get('cart_item_id')
                user_id = event_body.get('user_id')
                cart_item = event_body.get('cart_item')
                print('cart_item_id:',cart_item_id)
                print('user_id:',user_id)
                print('cart_item:',cart_item)
                print("Inside cart 1")
                add_to_cart(cart_item_id, cart_item, user_id)
                print("Inside cart 2")
                return {
                    'statusCode': 200,
                    'body': json.dumps('Product added to cart successfully', cls=DecimalEncoder)
                }
            elif operation == 'get_all_products': 
                products = get_all_products()
                return {
                    'statusCode': 200,
                    'body': json.dumps(products, cls=DecimalEncoder)
                }
            elif operation == 'get_order_details': 
                orders = get_order_details()
                return {
                    'statusCode': 200,
                    'body': json.dumps(orders, cls=DecimalEncoder)
                }
            elif operation == 'create_order':  # Get all Products
                cart_item_id = event_body.get('cart_item_id')
                user_id = event_body.get('user_id')
                cart_item = event_body.get('cart_item')
                order_id = event_body.get('order_id')
                delivery_address = event_body.get('delivery_address')
                checkout_price = event_body.get('checkout_price')
                email = event_body.get('email')
                discount_price = event_body.get('discount_price')
                tax = event_body.get('tax')
                shipping_cost = event_body.get('shipping_cost')
                net_total = event_body.get('net_total')
                response = create_order(order_id, user_id, cart_item, cart_item_id, delivery_address, checkout_price, email, discount_price, tax, shipping_cost, net_total)
                send_email_notification(order_id, email)
                print("Inside order 3")
                return {
                    'statusCode': 200,
                    'body': json.dumps(response, cls=DecimalEncoder)
                }
            elif operation == 'remove_from_cart':
                cart_item_id_remove = event_body.get('cart_item_id')
                response = remove_from_cart(cart_item_id_remove)
                return {
                    'statusCode': 200,
                    'body': json.dumps('response', cls=DecimalEncoder)
                }
            elif operation == 'get_user_cart': 
                user_id = event_body.get('user_id')
                user_cart = get_user_cart(user_id)
                print('user_id:',user_id)
                print('user_cart:',user_cart)
                return {
                    'statusCode': 200,
                    'body': json.dumps(user_cart, cls=DecimalEncoder)
                }
            else:
                return {
                    'statusCode': 400,
                    'body': json.dumps('Invalid operation')
                }
        else:
            return {
                'statusCode': 400,
                'body': json.dumps('Operation not specified')
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Error: {}'.format(str(e))})
        }
