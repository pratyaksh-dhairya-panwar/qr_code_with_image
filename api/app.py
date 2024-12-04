# api/app.py

import os
from flask import Flask, render_template, request
import qrcode
from PIL import Image, ImageDraw, ImageOps
from io import BytesIO
import base64

app = Flask(__name__, template_folder='../templates', static_folder='../static')

def generate_qr(url, image_file=None, fill_color="black", back_color="white", grayscale=False):
    """Generate a QR code with an optional central image."""
    # Create QR code with high error correction
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H
    )
    qr.add_data(url)
    qr.make(fit=True)

    # Generate QR code image with specified colors
    qr_img = qr.make_image(fill_color=fill_color, back_color=back_color).convert('RGBA')

    if image_file:
        # Open the uploaded image and convert to RGBA
        logo = Image.open(image_file).convert('RGBA')

        if grayscale:
            # Convert logo to grayscale
            logo = logo.convert('L').convert('RGBA')

        # Calculate the size of the logo area
        qr_width, qr_height = qr_img.size
        logo_size = qr_width // 4  # The logo area is 25% of the QR code size

        # Define padding around the logo
        padding = 10  # Adjust this value as needed

        # Create a square canvas for the logo area with padding
        logo_canvas = Image.new('RGBA', (logo_size, logo_size), back_color)

        # Resize the logo to fit within the canvas minus padding
        max_logo_size = logo_size - 2 * padding
        logo.thumbnail((max_logo_size, max_logo_size), Image.LANCZOS)

        # Calculate position to center the logo on the canvas
        logo_pos_on_canvas = (
            (logo_canvas.width - logo.width) // 2,
            (logo_canvas.height - logo.height) // 2
        )

        # Paste the logo onto the canvas
        logo_canvas.paste(logo, logo_pos_on_canvas, logo)

        # Calculate position to center the logo canvas on the QR code
        qr_logo_pos = (
            (qr_width - logo_canvas.width) // 2,
            (qr_height - logo_canvas.height) // 2
        )

        # Draw a rectangle on the QR code where the logo will be placed
        draw = ImageDraw.Draw(qr_img)
        left = qr_logo_pos[0]
        top = qr_logo_pos[1]
        right = left + logo_canvas.width
        bottom = top + logo_canvas.height
        draw.rectangle([left, top, right, bottom], fill=back_color)

        # Paste the logo canvas onto the QR code
        qr_img.paste(logo_canvas, qr_logo_pos, logo_canvas)

    else:
        # If no image, ensure the center has a rectangle with back_color
        qr_width, qr_height = qr_img.size
        center_size = qr_width // 4  # 25% of the QR code size
        left = (qr_width - center_size) // 2
        top = (qr_height - center_size) // 2
        right = left + center_size
        bottom = top + center_size

        draw = ImageDraw.Draw(qr_img)
        draw.rectangle([left, top, right, bottom], fill=back_color)

    return qr_img

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get the URL from the form
        url = request.form.get('url')
        if not url:
            return render_template('index.html', error="Please enter a URL.")

        # Get the color mode from the form
        color_mode = request.form.get('color_mode', 'black_white')

        if color_mode == 'black_white':
            fill_color = 'black'
            back_color = 'white'
            grayscale = True
        else:
            fill_color = request.form.get('fill_color') or '#000000'
            back_color = request.form.get('back_color') or '#FFFFFF'
            grayscale = False

        # Process the uploaded image in memory
        image_file = request.files.get('image')
        if image_file and image_file.filename == '':
            image_file = None

        # Generate the QR code
        qr_img = generate_qr(url, image_file, fill_color, back_color, grayscale)

        # Save QR code image to a BytesIO object
        img_io = BytesIO()
        qr_img.save(img_io, 'PNG')
        img_io.seek(0)

        # Encode the image to base64 to send to the template
        img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')

        return render_template('index.html', qr_code=img_base64)

    return render_template('index.html')

# Vercel requires the app object to be named 'app' in api files
# No need to run app.run()

