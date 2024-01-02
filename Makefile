# Makefile for weewx badger

run:
	mpremote run main.py

deploy:
	mpremote fs cp main.py :main.py