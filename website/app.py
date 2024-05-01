from flask import Flask, render_template, request, redirect, url_for, flash, session
import boto3

app = Flask(__name__)
app.secret_key = "1234"

# AWS DynamoDB setup
dynamodb = boto3.resource('dynamodb')
login_table = dynamodb.Table('login')
music_table = dynamodb.Table('music') 
subscription_table = dynamodb.Table('subscriptions')

# Index page
@app.route('/')
def index():
    if session.get('user_name'):
        return redirect(url_for('main'))
    return render_template('login.html')

# Login page
@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    
    # Check if the user exists in the login table
    response = login_table.get_item(
        Key={
            'email': email
        }
    )
    
    # check if password matches the one stored in the login table for selected user
    if 'Item' in response:
        user = response['Item']
        if user.get('password') == password:
            session['email'] = email
            session['user_name'] = user.get('user_name')
            # redirect to main page with user_name
            return redirect(url_for('main'))
    
    # Authentication failed, show error message
    flash("Email or password is invalid.")
    return redirect(url_for('index'))

# Route to render the registration form
@app.route('/register', methods=['GET'])
def show_register_form():
    return render_template('register.html')

# Register route
@app.route('/register', methods=['POST'])
def register():
    # Retrieve registration form parameters
    email = request.form.get('email')
    username = request.form.get('username')
    password = request.form.get('password')

    # Check if the email already exists in the login table
    response = login_table.get_item(
        Key={
            'email': email
        }
    )
    if 'Item' in response:
        # If the email already exists, show error message
        flash('The email already exists.')
        return redirect(url_for('register'))

    # If the email is unique, add the new user information to the login table
    login_table.put_item(
        Item={
            'email': email,
            'user_name': username,
            'password': password
        }
    )

    # Redirect the user to the login page with a success message
    flash('Registration successful. Please log in.')
    return redirect(url_for('index'))


# Logout and redirect user to Index
@app.route('/logout')
def logout():
    session.pop('email')
    session.pop('user_name')
    return redirect(url_for('index'))

# Main content page
@app.route('/main')
def main():
    user_name = session.get('user_name')
    if user_name:
        # Get subscribed music information for the user from DynamoDB
        response = subscription_table.scan(
            FilterExpression='email = :email',
            ExpressionAttributeValues={':email': session.get('email')}
        )
        subscribed_music = response.get('Items', [])

        # Create an empty list to store music items
        queried_music = []

        # Iterate over subscribed music items
        for music_item in subscribed_music:
            title = music_item.get('title')

            # Query music_table for items with the same title
            response = music_table.scan(
                FilterExpression='title = :title',
                ExpressionAttributeValues={':title': title}
            )
            queried_music.extend(response.get('Items', []))

        # render the main page with a list of subscribed music
        return render_template('main.html', user_name=user_name, subscribed_music=queried_music)
    else:
        # If user_name is not present in the session data, redirect to the login page
        return redirect(url_for('index'))

# used to query the database
@app.route('/query', methods=['POST'])
def query():
    # Retrieve query parameters from the form
    title = request.form.get('title')
    music_year = request.form.get('year')
    artist = request.form.get('artist')

    # Construct the filter expression based on the provided parameters
    filter_expression = ''
    expression_attribute_values = {}
    expression_attribute_names = {}
    if title:
        filter_expression += 'contains(title, :title)'
        expression_attribute_values[':title'] = title
    if music_year:
        if filter_expression:
            filter_expression += ' AND '
        filter_expression += '#yr = :music_year'
        expression_attribute_values[':music_year'] = music_year
        expression_attribute_names['#yr'] = 'year'
    if artist:
        if filter_expression:
            filter_expression += ' AND '
        filter_expression += 'contains(artist, :artist)'
        expression_attribute_values[':artist'] = artist

    results = []

    # Query music_table based on the filter expression
    if filter_expression:
        scan_params = {
            'FilterExpression': filter_expression,
            'ExpressionAttributeValues': expression_attribute_values
        }
        if expression_attribute_names:
            scan_params['ExpressionAttributeNames'] = expression_attribute_names
        
        response = music_table.scan(**scan_params)
        queried_music = response.get('Items', [])

        # if user is already subscribed, add a condition
        # Iterate over the queried music
        for music_item in queried_music:
            if check_subscription(music_item.get('title')):
                music_item['subscribed'] = 'yes'
            else:
                music_item['subscribed'] = 'no'
            results.append(music_item)

    # Render the template with the queried music
    return render_template('query_results.html', queried_music=results)


# Subscribe to a song
@app.route('/subscribe', methods=['POST'])
def subscribe():
    # Get parameters from the form
    music_title = request.form.get('music_title')
    music_artist = request.form.get('music_artist')

    # check if subscription already exists
    if check_subscription(music_title):
        # Redirect back to the query result page
        return redirect(url_for('main'))
    
    # Add the subscribed music information to subscription table
    subscription_table.put_item(
        Item={
            'title': music_title,
            'email': session.get('email')
        }
    )
    
    # Redirect back to the main page
    return redirect(url_for('main'))

# ubsubscribe from a song
@app.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    # Retrieve the music ID from the form data
    music_title = request.form.get('music_title')

    # Retrieve user's email from session
    email = session.get('email')

    if email:
        # Delete the subscription item from the DynamoDB table
        try:
            subscription_table.delete_item(
                Key={
                    'title': music_title,
                    'email': session.get('email')
                }
            )
            print('Successfully unsubscribed from the music.')
        except Exception as e:
            print(f'Failed to unsubscribe: {str(e)}')
    else:
        print('User not logged in.')

    # Redirect the user to the main page
    return redirect(url_for('main'))

# check if the user is subscribed to the specified title
def check_subscription(title):
    try:
        # Get subscribed music information for the user from DynamoDB
        response = subscription_table.scan(
            FilterExpression='email = :email',
            ExpressionAttributeValues={':email': session.get('email')}
        )
        subscribed_music = response.get('Items', [])

        # Check if song already exists in the users subscriptions
        for music_item in subscribed_music:
            if music_item['title'] == title:
                # return true if it already exists
                return True

        # return false if song doesn't exist
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

if __name__ == "__main__":
    app.run(debug=True, port=8000)
