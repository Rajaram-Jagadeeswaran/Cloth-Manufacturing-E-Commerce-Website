import boto3
import subprocess

region_name = 'sa-east-1'
account_id = '250738637992'

orders_table_name = 'x22239243_orders'
cart_table_name = 'x22239243_cart'
product_table_name= 'x22239243_Products'
orders_table_primary_key_name = 'order_id'
cart_table_primary_key_name = 'cart_item_id'
product_table_primary_key_name = 'product_id'
primary_key_type = 'S'
gsi_name = 'user_id-index'
gsi_key_name = 'user_id'
gsi_key_type = 'S'

target_utilization = 70
read_capacity_low = 1
read_capacity_high = 10
write_capacity_low = 1
write_capacity_high = 10

bucket_name = 'x22239243-cpp-project-bucket'
bucket_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "s3:PutObject",
            "Resource": f"arn:aws:s3:::{x22239243-cpp-project-bucket}/*"
        }
    ]
}

topic_name = 'x22239243_a-max_mailing_system'
email_address = 'x22239243@student.ncirl.ie'

eb_app_name = 'x22239243-cpp-application-prod'
eb_env_name = 'x22239243-cpp-application-env'

def create_table(table_name, primary_key_name, primary_key_type, gsi_name, gsi_key_name, gsi_key_type):
    dynamodb = boto3.resource('dynamodb', region_name=region_name)

    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[{'AttributeName': primary_key_name, 'KeyType': 'HASH'}],
        AttributeDefinitions=[
            {'AttributeName': primary_key_name, 'AttributeType': primary_key_type},
            {'AttributeName': gsi_key_name, 'AttributeType': gsi_key_type}
        ],
        ProvisionedThroughput={'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1},
        GlobalSecondaryIndexes=[
            {
                'IndexName': gsi_name,
                'KeySchema': [{'AttributeName': gsi_key_name, 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'},
                'ProvisionedThroughput': {'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1},
            }
        ],
        BillingMode='PROVISIONED',
        StreamSpecification={'StreamEnabled': False},
        SSESpecification={'Enabled': False},
    )
    
    return f"Table '{table_name}' created successfully."


def create_s3_bucket(bucket_name):
    s3 = boto3.client('s3', region_name=region_name)
    
    s3.create_bucket(
        Bucket=bucket_name,
        ACL='private',
        CreateBucketConfiguration={
            'LocationConstraint': 'sa-east-1'
        },
    )

    s3.put_bucket_policy(
        Bucket=bucket_name,
        Policy=str(bucket_policy).replace("'", '"')
    )

    return f"S3 bucket '{bucket_name}' created successfully with public access and bucket policy."

def disable_public_access(bucket_name):
    s3 = boto3.client('s3', region_name=region_name)
    
    s3.put_public_access_block(
        Bucket=bucket_name,
        PublicAccessBlockConfiguration={
            'BlockPublicAcls': False,
            'IgnorePublicAcls': False,
            'BlockPublicPolicy': False,
            'RestrictPublicBuckets': False
        }
    )

    return f"Public access disabled for the S3 bucket '{bucket_name}'."
    
def create_sns_topic(topic_name, email_address):
    sns_client = boto3.client('sns', region_name=region_name)
    response = sns_client.create_topic(Name=topic_name)
    topic_arn = response['TopicArn']

    subscription_response = sns_client.subscribe(
        TopicArn=topic_arn,
        Protocol='email',
        Endpoint=email_address
    )
    
    return f"SNS topic '{topic_name}' created successfully and email subsription to {email_address} created successfully."
    
def run_aws_cli_command(command):
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running AWS CLI command: {e}")
        print("Error Output:")
        print(e.stderr)

try:
    orders_table_response = create_table(orders_table_name, orders_table_primary_key_name, primary_key_type, gsi_name, gsi_key_name, gsi_key_type)
    print(orders_table_response)

    cart_table_response = create_table(cart_table_name, cart_table_primary_key_name, primary_key_type, gsi_name, gsi_key_name, gsi_key_type)
    print(cart_table_response)
    
    product_table_response = create_table(product_table_name, product_table_primary_key_name, 'N')
    print(product_table_response)

    s3_buket_response = create_s3_bucket(bucket_name)
    print(s3_buket_response)
    
    s3_public_access_response = disable_public_access(bucket_name)
    print(s3_public_access_response)
    
    sns_topic_respone = create_sns_topic(topic_name,email_address)
    print(sns_topic_respone)
    
    install_eb_cli_command = ['pip', 'install', 'awsebcli']
    run_aws_cli_command(install_eb_cli_command)
    
    eb_init_command = ['eb', 'init', '-p', 'python-3.11', eb_app_name, '--region', 'ea-east-1']
    run_aws_cli_command(eb_init_command)
    
    eb_create_command = ['eb', 'create', eb_env_name, '--single']
    run_aws_cli_command(eb_create_command)
    
except Exception as e:
    print(f"Error: {e}")