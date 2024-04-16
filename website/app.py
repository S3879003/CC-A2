from flask import Flask, render_template, request, redirect, url_for, flash
import boto3

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for flashing messages

# AWS DynamoDB setup
dynamodb = boto3.resource('dynamodb')
login_table = dynamodb.Table('login')  # Replace 'login' with your table name
music_table = dynamodb.Table('music')  # Replace 'music' with your table name

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    
    # Check if the user exists in DynamoDB
    response = login_table.get_item(
        Key={
            'email': email
        }
    )
    
    if 'Item' in response:
        user = response['Item']
        if user.get('password') == password:
            # Authentication successful, redirect to main page with user_name
            return redirect(url_for('main', user_name=user.get('username')))
    
    # Authentication failed, show error message
    flash("Email or password is invalid.")
    return redirect(url_for('index'))

@app.route('/main')
def main():
    user_name = request.args.get('user_name')
    if user_name:
        # Get subscribed music information for the user from DynamoDB
        response = music_table.scan(
            FilterExpression='user_name = :user_name',
            ExpressionAttributeValues={':user_name': user_name}
        )
        subscribed_music = response.get('Items', [])
        return render_template('main.html', user_name=user_name, subscribed_music=subscribed_music)
    else:
        # If user_name is not provided in the URL, redirect to login page
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
