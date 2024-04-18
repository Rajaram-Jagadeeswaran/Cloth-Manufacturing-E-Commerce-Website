import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table_name = 'CouponCodes'
table = dynamodb.Table(table_name)

def validate_coupon_code(coupon_code):
    # Query DynamoDB table to check if the coupon code exists and is still valid
    response = table.get_item(
        Key={
            'coupon_code': coupon_code
        }
    )
    if 'Item' not in response:
        return False, "Invalid coupon code"
    
    coupon_details = response['Item']
    current_time = datetime.now().isoformat()
    
    if current_time > coupon_details['validity_period']:
        return False, "Coupon code has expired"
    
    if coupon_details['usage_limit'] <= 0:
        return False, "Coupon code has reached its usage limit"
    
    return True, coupon_details

def apply_coupon_to_order(order_total, coupon_details):
    discount_amount = coupon_details['discount_amount']
    new_total = order_total - (order_total * discount_amount / 100)
    return new_total

# Example usage:
def checkout_with_coupon(coupon_code, order_total):
    valid, coupon_details = validate_coupon_code(coupon_code)
    if valid:
        updated_total = apply_coupon_to_order(order_total, coupon_details)
        return f"Coupon applied successfully! Updated total: {updated_total}"
    else:
        return coupon_details

# Test
coupon_code = "ABCDE123"
order_total = 100
print(checkout_with_coupon(coupon_code, order_total))

# Example interaction:
def user_checkout_interaction():
    coupon_code = input("Enter coupon code (if any): ")
    order_total = float(input("Enter order total: "))
    
    result = checkout_with_coupon(coupon_code, order_total)
    print(result)

# Test
user_checkout_interaction()
