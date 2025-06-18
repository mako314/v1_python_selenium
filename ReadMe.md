## Basic Use

### Install requirements.txt

Install dependencies in virtual env using the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

### Run virtual environment

**Unix/macOS:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### Run script with option flags

You can run the script with the following optional flags:

- `-rc` or `--result-count` : *Integer* — number of results you'd like returned  
- `-s` or `--search` : *String* — term you'd like searched  
- `-c` or `--clean` : Clears the logs before starting

**Example:**
```bash
python script.py --search "example query" --result-count 10 --clean
```

```bash
python3 google_results.py -c -rc 10 -s nvidia
```
