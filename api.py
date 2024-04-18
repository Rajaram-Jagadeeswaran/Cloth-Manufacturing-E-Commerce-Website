import boto3
import uuid
import random
import string
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb')
table_name = 'CouponCodes'
table = dynamodb.Table(table_name)

def generate_coupon_code(length=8):
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for _ in range(length))

def create_coupon_code(discount_amount, validity_days, usage_limit):
    coupon_code = generate_coupon_code()
    validity_period = datetime.now() + timedelta(days=validity_days)
    
    # Store coupon code in DynamoDB table
    response = table.put_item(
        Item={
            'coupon_code': coupon_code,
            'discount_amount': discount_amount,
            'validity_period': validity_period.isoformat(),
            'usage_limit': usage_limit
        }
    )
    
    return coupon_code

def lambda_handler(event, context):
    # Example usage: create a coupon code with a 20% discount, valid for 30 days, and usage limit of 100
    discount_amount = 20
    validity_days = 30
    usage_limit = 100
    coupon_code = create_coupon_code(discount_amount, validity_days, usage_limit)
    
    return {
        'statusCode': 200,
        'body': f'Coupon code "{coupon_code}" created successfully!'
    }
