<div align="center">
  <img src="https://i.ibb.co/wNm5kJn4/1765831046347-2.jpg" alt="Raj AI Bot Banner" style="border: 4px solid #333; border-radius: 8px; width: 100%; max-width: 900px;">
</div>
<br>

# 🤖 Raj AI Bot - Advanced Telegram Assistant

![Python](https://img.shields.io/badge/Python-3.10-blue?style=for-the-badge&logo=python)
![RAJ](https://img.shields.io/badge/%20RAJ-LLM-MODEL-orange?style=for-the-badge&logo)
![MongoDB](https://img.shields.io/badge/DB-MongoDB-green?style=for-the-badge&logo=mongodb)

A production-grade, asynchronous Telegram Bot powered by Google's Gemini AI.
Designed for 24/7 uptime with "Smart Delay" to mimic human interaction and a Hybrid Memory system.

## 🚀 Features

* **🧠 RAJ LLM MODEL**: Intelligent conversations using RAJ LLM MODEL.30.
* **⚡ Hybrid Memory**: Falls back to JSON responses if Rate Limited (1 req/min).
* **🗣️ Voice Intelligence**: Converts Voice Notes to Text, understands them, and replies with Audio.
* **🎨 Image Engine**: Generates images from text and analyzes photos sent by users.
* **🛡️ Security System**: Password-protected Admin commands (`/Raj` trigger).
* **📢 Broadcast System**: Send messages to all users in the MongoDB database.
* **💤 Smart Delay**: Artificial delay (15s) to make the bot feel human.
* **🌍 24/7 Keep-Alive**: Integrated Web Server (Port 8080) for cloud deployment.

## 🛠️ Configuration (.env)

Create a `.env` file in the root directory:

```env
BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
API_ID=123456
API_HASH=a1b2c3d4e5f6g7h8i9j0
GEMINI_API_KEY=AIzaSy...
MONGO_URI=mongodb+srv://username:password@cluster0.mongodb.net/?retryWrites=true&w=majority
ADMIN_ID=123456789
PORT=8080
