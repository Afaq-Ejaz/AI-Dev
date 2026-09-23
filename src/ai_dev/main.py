import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from google import genai

load_dotenv()
app = FastAPI()
