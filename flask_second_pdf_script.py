import os
import base64
import logging
from time import sleep
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

download_dir = os.getcwd()
prefs = {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,  # Disable Save As dialog
    "plugins.always_open_pdf_externally": True,  # Open PDFs in Chrome's viewer
}
options = Options()
options.add_argument("--headless")
options.add_argument("--start-maximized")
options.add_experimental_option("prefs", prefs)

# Your 2captcha API key
api_key = '60deff821f12d0ac054bd3da75b38332'  # Replace with your 2Captcha API key


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
@app.route('/get_second_pdf', methods=['POST'])
def get_pdf():
    data = request.json
    rfc = data.get('RFC')
    ciec = data.get('CIEC')

    if not rfc or not ciec:
        return jsonify({"error": "RFC and CIEC are required"}), 400

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get('https://wwwmat.sat.gob.mx/app/seg/faces/pages/lanzador.jsf?url=/operacion/43824/reimprime-tus-acuses-del-rfc&tipoLogeo=c&target=principal&hostServer=https://wwwmat.sat.gob.mx')

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

            WebDriverWait(driver, 40).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id = 'action_bar2']"))
            )
            logging.info(f"Login successful for user: {rfc}")
            print("In download PDF function.")
            driver.refresh()

            # Locate the iframe and get the `src` attribute
            button_iframe = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//iframe[@id = 'iframetoload']"))
            )
            driver.switch_to.frame(button_iframe)

            button_pdf = WebDriverWait(driver, 40).until(
                EC.presence_of_element_located((By.XPATH, "//button[@id = 'formReimpAcuse:j_idt50']"))
            )

            # Click the button
            button_pdf.click()
            sleep(10)  # Wait for the download to complete

            # Find the most recently downloaded PDF
            files = [f for f in os.listdir(download_dir) if f.endswith(".pdf")]
            if files:
                latest_file = max(files, key=lambda f: os.path.getctime(os.path.join(download_dir, f)))
                pdf_path = os.path.join(download_dir, latest_file)

                # Convert PDF to Base64
                with open(pdf_path, "rb") as pdf_file:
                    base64_pdf = base64.b64encode(pdf_file.read()).decode("utf-8")

                # Optionally, delete the local file after conversion
                os.remove(pdf_path)
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
    app.run(host='0.0.0.0', port=5001, debug=True)
