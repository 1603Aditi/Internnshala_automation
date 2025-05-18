from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import pandas as pd
import os
from dotenv import load_dotenv
from selenium.webdriver.common.keys import Keys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_confirmation_email(receiver_email, internship_count):
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("EMAIL_PASSWORD")

    subject = "Internshala Bot: Application Submitted"
    body = f"Hello,\n\nOur bot has successfully applied to {internship_count} internships on your behalf.\n\nBest of luck!\n\n— Internshala Bot"

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
            print("Confirmation email sent!")
    except Exception as e:
        print("Email sending failed:", str(e))


load_dotenv()
EMAIL = os.environ['EMAIL']
PASSWORD = os.environ['PASSWORD']

keywords = os.environ["KEYWORDS"].split(",")
min_stipend = int(os.environ["MIN_STIPEND"])
max_duration = int(os.environ["MAX_DURATION"])

chrome_options = Options()
driver = webdriver.Chrome(options=chrome_options)
driver.maximize_window()
driver.get("https://internshala.com/login")

sleep(2)

email_field=WebDriverWait(driver,10).until(EC.presence_of_element_located((By.NAME,"email")))
email_field.send_keys(EMAIL)
sleep(1)
password_field=WebDriverWait(driver,10).until(EC.presence_of_element_located((By.NAME,"password")))
password_field.send_keys(PASSWORD+Keys.ENTER)
sleep(5)

internships_tab = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="internships_new_superscript"]'))
)
internships_tab.click()

sleep(2) 

data = []

def is_relevant(title, duration, stipend, keywords):
    title_lower = title.lower()
    if not any(keyword in title_lower for keyword in keywords):
        return False
    if "month" in duration.lower():
        try:
            months = int(duration.lower().split("month")[0].strip())
            if months > max_duration:
                return False
        except:
            pass 

    if "unpaid" in stipend.lower():
        return False

    try:
        amount = int(''.join(filter(str.isdigit, stipend)))
        if amount < min_stipend:
            return False
    except:
        pass

    return any(keyword in title.lower() for keyword in keywords)


relevant_links = []
relevant_internships = []

for _ in range(10):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    sleep(3) 

internships = driver.find_elements(By.CLASS_NAME, "individual_internship")

for internship in internships:
    try:
        title = internship.find_element(By.CSS_SELECTOR, ".job-title-href").text
    except:
        title = ""

    try:
        company = internship.find_element(By.CSS_SELECTOR, ".company-name").text
    except:
        company = ""

    try:
        location = internship.find_element(By.CSS_SELECTOR, ".row-1-item.locations span a").text
    except:
        location = ""

    try:
        duration = internship.find_elements(By.CSS_SELECTOR, ".row-1-item span")[1].text
    except:
        duration = ""

    try:
        stipend = internship.find_element(By.CSS_SELECTOR, ".row-1-item .stipend").text
    except:
        stipend = ""
    

    if is_relevant(title, duration, stipend, keywords):
        data_href = internship.get_attribute("data-href")
        full_url = "https://internshala.com" + data_href
        relevant_internships.append({
            "title": title,
            "company": company,
            "duration": duration,
            "stipend": stipend,
            "url": full_url
        })
        if full_url not in relevant_links:
            relevant_links.append(full_url)
            print(f"Relevant internship found: {title} at {company}")
            print(f"Saved link: {full_url}")


for url in relevant_links:
    try:
        driver.get(url)
        apply_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-primary.top_apply_now_cta"))
        )
        apply_button.click()
        sleep(5)
        print("Applied successfully to:", url)
        driver.get("https://internshala.com/internships/matching-preferences/")

    except Exception as e:
        print("Apply button click failed for", url, "Error:", e)

print("Total relevant internships:", len(relevant_internships))
if len(relevant_internships) > 0:
    df = pd.DataFrame(relevant_internships)
    df.rename(columns={
        'title': 'Title',
        'company': 'Company',
        'duration': 'Duration',
        'stipend': 'Stipend',
        'url': 'URL'
    }, inplace=True)
    df.to_csv("internshala_internships.csv", index=False)
    print("CSV file saved successfully.")
    receiver_email = os.getenv("RECEIVER")
    print("Receiver Email:", receiver_email)
    send_confirmation_email(receiver_email, len(relevant_internships))
else:
    print("No relevant internships found, CSV file will be empty.")




driver.quit()