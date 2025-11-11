from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

CHROME_BINARY = "/usr/bin/google-chrome-stable"
CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"

print("Usando CHROME_BINARY =", CHROME_BINARY)
print("Usando CHROMEDRIVER_PATH =", CHROMEDRIVER_PATH)

options = Options()
options.binary_location = CHROME_BINARY
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--incognito")

service = Service(CHROMEDRIVER_PATH)

driver = webdriver.Chrome(service=service, options=options)
print("✅ Driver creado correctamente")
driver.get("https://www.google.com")
input("Pulsa ENTER para cerrar...")
driver.quit()

