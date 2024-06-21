import discord
import requests
import base64
import os
import mysql.connector
import json
from typing import Any
import cv2
import numpy as np
import base64
from io import BytesIO
from PIL import Image

API_KEY = os.environ["OPEN_AI_TOKEN"]
MYSQL_HOST = os.getenv('MYSQL_HOST')
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE')

def get_db_connection():
    connection = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE
    )
    return connection

def insert_data(data, discord_account, discord_username):
    try:
        user_exists = check_user_exists(discord_account)
        print(f"User exists: {user_exists}")

        if not user_exists:
            create_user(discord_account, discord_username)
            print("User created successfully: ", discord_account)

        insert_game_and_guesses(data, discord_account)
        
    except mysql.connector.Error as error:
        print("Error accessing to DB :", error)


def insert_game_and_guesses(data, discord_account):
    total_guesses = len(data)
    date = None
    correct_word = None  
    connection = get_db_connection()
    cursor = connection.cursor()

    insert_game_query = "INSERT INTO games (discordAccount, totalGuesses, date, correctWord) VALUES (%s, %s, %s, %s)"
    
    cursor.execute(insert_game_query, (discord_account, total_guesses, date, correct_word))
    
    game_id = cursor.lastrowid


    for choice in data:
        word_guess = ''.join(choice['guess'])
        color_array = choice['color']
        
        if all(color == 'green' for color in color_array):

            correct_word = word_guess
            print("Correct word found: ", correct_word)
            
        result1, result2, result3, result4, result5 = color_array
        insert_guess_query = "INSERT INTO guesses (gameId, word, result1, result2, result3, result4, result5) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        
        cursor.execute(insert_guess_query, (game_id, word_guess, result1, result2, result3, result4, result5))
        
        print(f"Guess inserted: {word_guess}, {result1}, {result2}, {result3}, {result4} successfully")

    
    update_correct_word_query = "UPDATE games SET correctWord = %s WHERE gameId = %s"
    
    cursor.execute(update_correct_word_query, (correct_word, game_id))
    print(f"Correct word updated: {correct_word} successfully")

    connection.commit()

    cursor.close()
    connection.close()

def create_user(discord_account, discord_username):
    connection = get_db_connection()

    cursor = connection.cursor()

    try: 
        insert_user_query = "INSERT INTO players (discordAccount, discordUsername) VALUES (%s, %s)"
        cursor.execute(insert_user_query, (discord_account, discord_username))

        connection.commit()

    except mysql.connector.Error as error:
        print("Error writing to DB:", error)

    finally:
        if 'cursor' in locals() and cursor is not None:
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()

def check_user_exists(discord_account):
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        query = "SELECT EXISTS(SELECT 1 FROM players WHERE discordAccount = %s)"
        cursor.execute(query, (discord_account,))
        result: Any = cursor.fetchone()

        return result[0] > 0

    except mysql.connector.Error as error:
        print("Error connecting to the DB:", error)
        return False

    finally:
        if 'cursor' in locals() and cursor is not None:
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()

def store_wordle_result(attempt, guess, colors, total_attempts):
    connection = get_db_connection()
    cursor = connection.cursor()

    add_result = ("INSERT INTO attempts "
                  "(attempt, guess, colors, total_attempts) "
                  "VALUES (%s, %s, %s, %s)")

    data_result = (attempt, json.dumps(guess), json.dumps(colors), total_attempts)

    cursor.execute(add_result, data_result)
    connection.commit()

    cursor.close()
    connection.close()

def process_gpt_response(response):
    response_cleaned = response.replace("```json", "").replace("```","")
    
    response_casted = json.loads(response_cleaned)
        
    for result in response_casted:
        attempt = result['attempt']
        guess = result['guess']
        colors = result['color']
        
        print("\n attempt: ", attempt)
        print("\n guess: ", guess)
        print("\n colors: ", colors)

        store_wordle_result(attempt, guess, colors, 0)

def encode_image(image_data):
    return base64.b64encode(image_data).decode('utf-8')

def image_to_base64(image):
    """Convert an OpenCV image to a base64 string."""
    _, buffer = cv2.imencode('.png', image)
    return base64.b64encode(buffer).decode('utf-8')

def base64_size_in_mb(base64_str):

    # Decode the base64 string
    binary_data = base64.b64decode(base64_str)

    # Calculate the size in bytes
    size_in_bytes = len(binary_data)

    # Convert to megabytes
    size_in_mb = size_in_bytes / (1024 * 1024)

    print(size_in_mb)
    return size_in_mb
    
def base64_to_image(base64_str):
    """Convert base64 string to an OpenCV image."""
    try:
        # Validate if the base64 string is correctly formatted
        if base64_str.startswith('data:image'):
            header, base64_str = base64_str.split(',', 1)

        # Decode the base64 string
        image_data = base64.b64decode(base64_str)
        image = Image.open(BytesIO(image_data))
        return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    except (base64.binascii.Error, UnidentifiedImageError) as e:
        raise ValueError(f"Failed to decode base64 string or identify image: {e}")

def process_image(base64_str):
    # Convert base64 string to image
    try:
        image = base64_to_image(base64_str)
    except ValueError as e:
        return str(e)

    # Define the color ranges
    # Aqua Forest (approx. green)
    aqua_forest_lower = np.array([40, 50, 50])
    aqua_forest_upper = np.array([80, 255, 255])

    # Goldenrod (approx. yellow)
    goldenrod_lower = np.array([20, 100, 100])
    goldenrod_upper = np.array([30, 255, 255])

    # Convert image to HSV color space
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Create masks for the color ranges
    aqua_forest_mask = cv2.inRange(hsv_image, aqua_forest_lower, aqua_forest_upper)
    goldenrod_mask = cv2.inRange(hsv_image, goldenrod_lower, goldenrod_upper)

    # Define the new colors in BGR (OpenCV uses BGR by default)
    new_green = np.array([0, 255, 0])  # Green
    new_yellow = np.array([0, 255, 255])  # Yellow

    # Change colors in the original image
    image[aqua_forest_mask > 0] = new_green
    image[goldenrod_mask > 0] = new_yellow

    print("Image processed successfully.")
    cv2.imwrite("./img.png", image)
    
    # Convert processed image back to base64
    base64_size_in_mb(image)
    return image_to_base64(image)
    
def ocr_image_initial(base64_image):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    payload = {
      "model": "gpt-4-turbo",
      "messages": [
        {
          "role": "user",
          "content": [
            {
              "type": "text",
              "text": "Analyze the provided Wordle image and extract the information about the letters and their colors for each attempt. Identify each letter in the Wordle grid and determine the color associated with each letter: gray for letters not in the word, light-yellow for letters in the word but in the wrong position, and light-green for letters in the correct position. Organize the extracted information into a JSON array where each object represents an attempt, containing \"attempt\" (the attempt number, starting from 0), \"guess\" (an array of letters guessed), and \"color\" (an array of corresponding colors). Use the following format as an example: [{\"attempt\": 0, \"guess\": [\"s\", \"p\", \"a\", \"c\", \"e\"], \"color\": [\"gray\", \"gray\", \"yellow\", \"gray\", \"yellow\"]}, {\"attempt\": 1, \"guess\": [\"a\", \"u\", \"n\", \"t\", \"y\"], \"color\": [\"yellow\", \"yellow\", \"gray\", \"yellow\", \"gray\"]}, {\"attempt\": 2, \"guess\": [\"g\", \"r\", \"o\", \"a\", \"t\"], \"color\": [\"green\", \"green\", \"gray\", \"green\", \"green\"]}, {\"attempt\": 3, \"guess\": [\"g\", \"l\", \"o\", \"a\", \"t\"], \"color\": [\"green\", \"green\", \"green\", \"green\", \"green\"]}]. The colors should be represented as strings: \"gray\" for letters not in the word, \"yellow\" for letters in the word but in the wrong position, and \"green\" for letters in the correct position. Only answer with the valid JSON message. Do not add any extra information",
            },
            {
              "type": "image_url",
              "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
              }
            }
          ]
        }
      ],
      "max_tokens": 600
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
  

    return response.json()

def convert_png_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string

def ocr_image(base64_image):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    example_base64_image = convert_png_to_base64("./example_image.png")
    
    example_interpretation = {
        "example_image": example_base64_image,
        "correct_interpretation": [
            {
                "attempt": 0,
                "guess": ["H", "A", "P", "P", "Y"],
                "color": ["gray", "gray", "yellow", "gray", "green"]
            },
            {
                "attempt": 1,
                "guess": ["P", "R", "I", "C", "E"],
                "color": ["green", "gray", "yellow", "gray", "yellow"]
            },
            {
                "attempt": 2,
                "guess": ["P", "I", "E", "T", "Y"],
                "color": ["green", "green", "green", "green", "green"]
            }
        ]
    }

    system_message = {
        "role": "system",
        "content": (
            "Analyze the provided Wordle image and extract the information about the letters and their colors for each attempt. "
            "Identify each letter in the Wordle grid and determine the color associated with each letter: gray for letters not in the word, "
            "yellow for letters in the word but in the wrong position, and green for letters in the correct position. "
            "Organize the extracted information into a JSON array where each object represents an attempt, containing \"attempt\" (the attempt number, starting from 0), "
            "\"guess\" (an array of letters guessed), and \"color\" (an array of corresponding colors). "
            "Use the following format as an example: [{\"attempt\": 0, \"guess\": [\"H\", \"A\", \"P\", \"P\", \"Y\"], \"color\": [\"gray\", \"gray\", \"yellow\", \"gray\", \"green\"]}]. "
            "The colors should be represented as strings: \"gray\" for letters not in the word, \"yellow\" for letters in the word but in the wrong position, and \"green\" for letters in the correct position. "
            "Only answer with the valid JSON message. Do not add any extra information. Here is an example image and its correct interpretation for reference: "
            f"{example_interpretation}"
        )
    }

    user_message = {
        "role": "user",
        "content": f"data:image/jpeg;base64,{base64_image}"
    }

    payload = {
        "model": "gpt-4-turbo",
        "messages": [system_message, user_message],
        "max_tokens": 600
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    return response.json()


intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Bot logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('/wordle') and message.attachments:
        attachment = message.attachments[0]

        if attachment.content_type.startswith('image'):
            
            image_response = requests.get(attachment.url)
            if image_response.status_code == 200:
                
                username = message.author.name
                discriminator = message.author.discriminator
                discord_username = message.author.display_name
                discord_account = f"{username}#{discriminator}"
                
                image_data = image_response.content
                
                #base64_image = encode_image(image_data)
                base64_image = process_image(encode_image(image_data))

                print(f"Discord Account: {discord_account} (Discord User: {discord_username})")

                #result = ocr_image(base64_image)['choices'][0]['message']['content']
                temp = ocr_image(base64_image)
                print(temp)
                result = ocr_image(base64_image)['choices'][0]['message']['content']

                response_cleaned = result.replace("```json", "").replace("```","")

                print(f"{response_cleaned}")
                
                #response_casted = json.loads(response_cleaned)          
                #insert_data(response_casted, discord_account, discord_username)


                await message.channel.send(result)
            else:
                await message.channel.send('Failed to download the image.')
        else:
            await message.channel.send('Please attach a valid image file.')

client.run(os.environ["TOKEN"])
