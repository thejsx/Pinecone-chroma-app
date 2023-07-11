import pytesseract
from PIL import Image
import pyautogui

def screenshot_text(box_height = 450, box_width = 1100, screen_height = 1080, screen_width = 1920):
    screenshot = pyautogui.screenshot()
    left = (screen_width-box_width)//2
    right = left + box_width
    upper = (screen_height - box_height)//2
    lower = upper + box_height

    cropped_image = screenshot.crop((left, upper, right, lower))

    # You can save the cropped image to verify it's correct
    cropped_image.save("cropped_image.png")

    # Use pytesseract to recognize the text
    pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
    qa_text = pytesseract.image_to_string(cropped_image)
    print(qa_text)
    return qa_text