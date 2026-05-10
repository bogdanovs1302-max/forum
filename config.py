import os

class Config:
    SECRET_KEY = 'your-secret-key-here'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///forum.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False