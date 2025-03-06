import os
import base64
import logging
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from twocaptcha import TwoCaptcha
import threading

app = Flask(__name__)

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

options = Options()
# options.add_argument("--headless")
options.add_argument("--start-maximized")
options.add_argument("--start-maximized")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--log-level=3")
options.add_experimental_option("useAutomationExtension", False)
options.add_experimental_option("excludeSwitches", ["enable-automation"])

# Your 2captcha API key
api_key = '2captcha_api_key'  # Replace with your 2Captcha API key


# Function to solve CAPTCHA
def solve_captcha(api_key, image_path):
    solver = TwoCaptcha(api_key)
    try:
        result = solver.normal(image_path)
        return result['code']
    except Exception as e:
        logging.error(f"Error solving CAPTCHA: {e}")
        return None


# Decode base64 image
def decode_base64_image(data_url, save_path):
    base64_str = data_url.split(',')[1]
    with open(save_path, 'wb') as file:
        file.write(base64.b64decode(base64_str))
    return save_path


def get_elem_by_xpath(driver, xpath, wait_time=3):
    try:
        elem = WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return elem
    except:
        return None


# Function to log in and get PDF
@app.route('/get_pdf', methods=['POST'])
def get_pdf():
    data = request.json
    rfc = data.get('RFC')
    ciec = data.get('CIEC')

    if not rfc or not ciec:
        return jsonify({"error": "RFC and CIEC are required"}), 400

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(
            'https://ptsc32d.clouda.sat.gob.mx/?/reporteOpinion32DContribuyente')

        contrasena = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//input[@id = 'contrasena']"))
        )

        contrasena.click()

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "Ecom_User_ID"))
        )

        driver.find_element(By.ID, "rfc").send_keys(rfc)
        driver.find_element(By.ID, "password").send_keys(ciec)

        captcha_image_data_url = get_elem_by_xpath(driver, "//label[@id='divCaptcha']/img").get_attribute('src')
        captcha_image_path = f'captcha_{threading.get_ident()}.jpg'
        decode_base64_image(captcha_image_data_url, captcha_image_path)

        captcha_solution = solve_captcha(api_key, captcha_image_path)
        if os.path.exists(captcha_image_path):
            os.remove(captcha_image_path)
        logging.info(captcha_solution)
        if captcha_solution:
            driver.find_element(By.XPATH, '//input[@id="userCaptcha"]').send_keys(captcha_solution)

            send_button = driver.find_element(By.ID, 'submit')
            send_button.click()

            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//iframe[@title = 'pdfReporteOpinion']"))
            )
            logging.info(f"Login successful for user: {rfc}")
            iframe = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//iframe[@title = 'pdfReporteOpinion']"))
            )
            src = iframe.get_attribute("src")

            if src.startswith("data:application/pdf;base64,"):
                base64_pdf = src.replace("data:application/pdf;base64,", "")
                driver.quit()
                return jsonify({"RFC": rfc, "PDF_Base64": base64_pdf})
            else:
                driver.quit()
                return jsonify({"error": "PDF not found"}), 500


        else:
            logging.info(f"Failed to solve CAPTCHA for user: {rfc}")
            driver.quit()
            return jsonify({"error": "Failed to process request"}), 500

    except Exception as e:
        logging.error(f"Error processing RFC {rfc}: {e}")
        driver.quit()
        return jsonify({"error": "Failed to process request"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
