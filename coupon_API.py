import boto3
import uuid
import json
import random
import string
from decimal import Decimal
from datetime import datetime, timedelta

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            if o % 1 == 0:
                return int(o)
            else:
                return float(o)
        return super(DecimalEncoder, self).default(o)

dynamodb = boto3.resource('dynamodb', region_name='sa-east-1')
coupon_table_name = 'X22239243CouponCodes'
table = dynamodb.Table(coupon_table_name)

def generate_coupon_code(length=8):
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for _ in range(length))

def create_coupon_code(coupon_id, discount_amount, validity_days, usage_limit):
    coupon_code = generate_coupon_code()
    validity_period = datetime.now() + timedelta(days=validity_days)
    
    # Store coupon code in DynamoDB table
    response = table.put_item(
        Item={
            'coupon_id': coupon_id,
            'coupon_code': coupon_code,
            'discount_amount': discount_amount,
            'validity_period': validity_period.isoformat(),
            'usage_limit': usage_limit
        }
    )
    
    return coupon_code
    
def get_coupon_details():
    try:
        response = table.scan()
        coupon_details = response['Items']
        return coupon_details

    except Exception as e:
        print(f'Error getting coupon details: {str(e)}')
        raise Exception(f'Error getting order details: {str(e)}')
        
def validate_coupon_code(coupon_code, order_total):
    try:
        response = table.scan()
        discount = response['Items']
        print(discount)
        
        for coupon in discount:
            if coupon['coupon_code'] == coupon_code:
                current_time = datetime.now().isoformat()
                
                if current_time > coupon['validity_period']:
                    return False, "Coupon code has expired"
                
                if coupon['usage_limit'] <= 0:
                    return False, "Coupon code has reached its usage limit"
                
                return True, coupon['discount_amount']
        
        # If the coupon code is not found in the table
        return False, "Invalid coupon code"
    
    except Exception as e:
        return False, str(e)

def apply_coupon_to_order(order_total, discount):
    print(order_total)
    discount_percentage = Decimal(discount)
    order_total_decimal = Decimal(order_total)
    discount_amount = order_total_decimal * (discount_percentage / Decimal(100))
    print(discount_amount)
    new_total = order_total_decimal - discount_amount
    print(new_total)
    return new_total

def lambda_handler(event, context):
    try:
        event_body = json.loads(event['body'])
        print('event_body =',event_body)
        operation = event_body.get('operation')
        print('operation =',operation)
        print('event =',event)
        
        if operation == 'create_coupon_code':
            coupon_id = str(uuid.uuid4())
            discount_amount = 20
            validity_days = 30
            usage_limit = 100
            coupon_code = create_coupon_code(coupon_id, discount_amount, validity_days, usage_limit)
            
            return {
                'statusCode': 200,
                'body': json.dumps({'message': f'Coupon code "{coupon_code}" created successfully!'}, cls=DecimalEncoder)
            }
        elif operation == 'get_coupon_details':
            coupon_details = get_coupon_details()
            print(coupon_details)
            return {
                'statusCode': 200,
                'body': json.dumps(coupon_details, cls=DecimalEncoder)
            }
        elif operation == 'validate_coupon':
            coupon_code = event_body.get('coupon_code')
            order_total = event_body.get('order_total')
            valid, discount = validate_coupon_code(coupon_code, order_total)
            print(coupon_code)
            print(order_total)
            print(valid)
            print(discount)
            
            if valid:
                # Assuming order_total is provided in the request body
                new_total = apply_coupon_to_order(order_total, discount) 
                print("inside func")
                print(new_total)
                
                return {
                    'statusCode': 200,
                    'body': json.dumps({'valid': True, 'discount': discount, 'new_total': new_total}, cls=DecimalEncoder)
                }
            else:
                return {
                    'statusCode': 200,
                    'body': json.dumps({'valid': False, 'message': discount}, cls=DecimalEncoder)
                }
                
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid operation specified'}, cls=DecimalEncoder)
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}, cls=DecimalEncoder)
        }
