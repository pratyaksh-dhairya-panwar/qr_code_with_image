import os
from flask import Flask, render_template, request, send_from_directory
import qrcode
from PIL import Image, ImageDraw, ImageOps
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # Max 5MB upload size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_qr(url, image_path=None, fill_color="black", back_color="white", grayscale=False):
    """Generate a QR code with an optional central image."""
    # Create QR code with high error correction
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H
    )
    qr.add_data(url)
    qr.make(fit=True)

    # Generate QR code image with specified colors
    qr_img = qr.make_image(fill_color=fill_color, back_color=back_color).convert('RGBA')

    if image_path:
        # Open the uploaded image and convert to RGBA
        logo = Image.open(image_path).convert('RGBA')

        if grayscale:
            # Convert logo to grayscale
            logo = ImageOps.grayscale(logo)
            logo = logo.convert('RGBA')  # Convert back to RGBA

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
            fill_color = request.form.get('fill_color', '#000000')
            back_color = request.form.get('back_color', '#FFFFFF')
            grayscale = False

        # Check if an image was uploaded
        file = request.files.get('image')
        image_path = None
        if file and file.filename != '':
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(image_path)
            else:
                return render_template('index.html', error="Unsupported file type.")

        # Generate the QR code
        qr_img = generate_qr(url, image_path, fill_color, back_color, grayscale)

        # Save the QR code image
        qr_filename = "qr_code.png"
        qr_path = os.path.join(app.config['UPLOAD_FOLDER'], qr_filename)
        qr_img.save(qr_path)

        return render_template('result.html', qr_image=qr_filename)

    return render_template('index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve the uploaded files."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

