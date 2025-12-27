# src package
import os
try:
	# Load .env if present so running from local dev shell without dot-sourcing still works
	from dotenv import load_dotenv
	dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
	if os.path.exists(dotenv_path):
		load_dotenv(dotenv_path)
except Exception:
	# dotenv is optional; if not installed we assume env vars are provided by the environment
	pass

