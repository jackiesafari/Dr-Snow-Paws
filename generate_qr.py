import qrcode
from PIL import Image

# Create QR code instance
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
)

# Add data
url = "http://192.168.60.235:8000"
qr.add_data(url)
qr.make(fit=True)

# Create an image from the QR Code
qr_image = qr.make_image(fill_color="black", back_color="white")

# Save the image
qr_image.save("Dr-Snow-Paws/static/qr_code.png")
print(f"QR code generated for URL: {url}") 