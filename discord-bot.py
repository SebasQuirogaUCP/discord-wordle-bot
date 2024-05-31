import discord
import requests
import base64
import os
import mysql.connector
import json
from typing import Any
from datetime import date


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

def insert_data(data, discord_account, discord_username, email, birthdate):
    try:
        user_exists = check_user_exists(discord_account)
        print(f"User exists: {user_exists}")

        if not user_exists:
            create_user(discord_account, discord_username, email, birthdate)
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


def create_user(discord_account, discord_username, email, birthdate):
    connection = get_db_connection()

    cursor = connection.cursor()

    try: 
        insert_user_query = "INSERT INTO players (discordAccount, discordUsername, email, birthdate) VALUES (%s, %s, %s, %s)"
        cursor.execute(insert_user_query, (discord_account, discord_username, email, birthdate))

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

def ocr_image(base64_image):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    payload = {
      "model": "gpt-4o",
      "messages": [
        {
          "role": "user",
          "content": [
            {
              "type": "text",
              "text": "You are an expert in OCR. You will receive an image of the results of a user playing Wordle. Your task is to extract all guesses and, if applicable, the color for each character, as the color is crucial for indicating whether the user got the correct letter (green), the correct letter in the wrong position (yellow) or the wrong possition and letter (black/gray). Read the letters horizontally from left to right and return the extracted data in an array of objects where each object represents a guess, containing its letters and their corresponding colors. Ignore any section showing a virtual phone keyboard and focus solely on the squares containing the guesses. Return the results in a valid JSON format. It is very important not to confuse the colors. JSON format with example: [{ attempt: 0, guess: [\"a\", \"b\", \"c\", \"d\", \"e\"], color: [\"black\", \"yellow\", \"green\", \"yellow\", \"black\"] }]."
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
      "max_tokens": 300
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

    if message.content.startswith('/ocr') and message.attachments:
        attachment = message.attachments[0]

        if attachment.content_type.startswith('image'):
            
            image_response = requests.get(attachment.url)
            if image_response.status_code == 200:
                image_data = image_response.content
                base64_image = encode_image(image_data)

                username = message.author.name
                discriminator = message.author.discriminator
                discord_username = message.author.display_name
                discord_account = f"{username}#{discriminator}"
                
                print(f"Discord Account: {discord_account} (Discord User: {discord_username})")

                result = ocr_image(base64_image)['choices'][0]['message']['content']

                print(result)

                response_cleaned = result.replace("```json", "").replace("```","")

                response_casted = json.loads(response_cleaned)
                           
                insert_data(response_casted, discord_account, discord_username, "email", date(2024, 5, 28))


                await message.channel.send(result)
            else:
                await message.channel.send('Failed to download the image.')
        else:
            await message.channel.send('Please attach a valid image file.')

client.run(os.environ["TOKEN"])
