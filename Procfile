web: curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py \
    | sed -e 's/allowed_executables = \["python", "python3"\]/allowed_executables = ["python3"]/' \
    | python3 \
    | indent && poetry run football-track flask --host 0.0.0.0
