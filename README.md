# Flask Selenium CAPTCHA Solver API

## Overview
This is a Flask-based API that automates login and PDF retrieval from the SAT (Servicio de Administración Tributaria) website using Selenium. It also solves CAPTCHAs using the 2Captcha service.

## Features
- Automates login using RFC and CIEC credentials.
- Solves CAPTCHA using the 2Captcha API.
- Extracts and returns a base64-encoded PDF.
- Uses headless Chrome with Selenium.

## Requirements
- Python 3.x
- Google Chrome
- ChromeDriver
- Flask
- Selenium
- WebDriver Manager
- 2Captcha API Key

## Installation

### 1. Clone the Repository
```sh
git clone https://github.com/Meesum-Raza/mendoza-project.git
```

### 2. Install Dependencies
```sh
pip install -r requirements.txt
```

## Usage
### Run the Flask Server
```sh
python app.py
```

### API Endpoint
#### `POST /get_pdf`
**Request Body (JSON):**
```json
{
  "RFC": "your_rfc",
  "CIEC": "your_ciec"
}
```

**Response (Success):**
```json
{
  "RFC": "your_rfc",
  "PDF_Base64": "<base64-encoded PDF>"
}
```

**Response (Failure):**
```json
{
  "error": "Failed to process request"
}
```


## License
This project is licensed under the MIT License.

## Author
Your Name - [GitHub Profile](https://github.com/yourusername)

