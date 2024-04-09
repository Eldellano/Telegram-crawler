#!/bin/bash

# применение миграций
echo "Migrate"
python main.py migrate

# пауза
echo "Sleep"
sleep 3

# запуск ротаций
echo "Rotate"
python main.py rotate
