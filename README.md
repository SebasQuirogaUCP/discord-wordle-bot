# 📸 Discord Wordle Bot with GPT-4o and Azure MySQL Service

Welcome to the Discord Wordle Bot! This bot uses OpenAI's GPT-4o model to perform OCR (Optical Character Recognition) on wordle images sent by users in a Discord server. The extracted text is stored in an Azure MySQL database.

## 🚀 Features

- 🟩⬛🟨 Wordle OCR on images sent by discord users
- 💬 Responds with the extracted text in the following format
```json
[
  {
    "attempt": 0,
    "guess": ["M", "O", "U", "R", "N"],
    "color": ["green", "black", "black", "black", "black"]
  },
  {
    "attempt": 1,
    "guess": ["S", "I", "L", "K", "Y"],
    "color": ["black", "black", "black", "black", "black"]
  },
  {
    "attempt": 2,
    "guess": ["W", "H", "E", "A", "T"],
    "color": ["black", "black", "black", "green", "green"]
  },
  {
    "attempt": 3,
    "guess": ["M", "A", "D", "A", "M"],
    "color": ["green", "green", "green", "green", "green"]
  }
]
```
- 💾 Stores results in Azure MySQL
- 🔒 Secure and scalable data storage

## 📋 Prerequisites

Before you begin, ensure you have the following:

1. **OpenAI API Key**: Sign up at [OpenAI](https://openai.com/) and get your API key.
2. **Discord Bot Token**: Create a bot on the [Discord Developer Portal](https://discord.com/developers/applications).
3. **Azure MySQL Credentials**: Set up an Azure MySQL instance.

## 🛠️ Installation

1. **Clone the Repository**

    ```bash
    git clone https://github.com/SebasQuirogaUCP/discord-wordle-bot.git
    cd discord-wordle-bot
    ```

2. **Install Dependencies**

    ```bash
    pip install discord.py requests pymysql
    ```

## 🏃‍♂️ Usage

1. **Run the Bot**

For testing purposes I would recommend to use [Replit](https://replit.com)

2. **Use the Bot in Discord**

    - Send a message with the `/ocr` command and attach an image file in your Discord server.
    - The bot will process the image, extract the text, store the result in the Azure MySQL database, and respond with the extracted text.

