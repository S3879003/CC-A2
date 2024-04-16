import boto3

def create_music_table():
    dynamodb = boto3.resource('dynamodb')
    
    # Define the table schema
    table = dynamodb.create_table(
        TableName='music',
        KeySchema=[
            {
                'AttributeName': 'title',
                'KeyType': 'HASH'  # Partition key
            },
            {
                'AttributeName': 'artist',
                'KeyType': 'RANGE'  # Sort key
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'title',
                'AttributeType': 'S'  # String
            },
            {
                'AttributeName': 'artist',
                'AttributeType': 'S'  # String
            }            
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )
    
    # Wait until the table exists
    table.meta.client.get_waiter('table_exists').wait(TableName='music')
    
    print("music Table has been created successfully.")

if __name__ == "__main__":
    create_music_table()
