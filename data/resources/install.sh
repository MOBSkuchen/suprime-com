$python -m venv .venv
curl -O http://suprime.sonvogel.com:5000/r/argument_parser.py
curl -O http://suprime.sonvogel.com:5000/r/main.py
curl -O http://suprime.sonvogel.com:5000/r/os_flags.py
curl -O http://suprime.sonvogel.com:5000/r/requirements.txt
.venv/bin/pip install -r requirements.txt
echo All done.
echo Run using '.venv/bin/python main.py <PATH>'