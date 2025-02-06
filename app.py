from flask import Flask, render_template, request, send_file, jsonify
from pydub import AudioSegment
from werkzeug.utils import secure_filename
import os
import random
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import io
import base64
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import math
from PIL import Image , ImageDraw


class Shape:
    def __init__(self, x, y , color , size=100):
        self.x = x
        self.y = y
        self.size = size
        self.color = color

    def draw(self,drawing):
        pass

class Square(Shape):
    def draw(self, drawing):
        drawing.rectangle([self.x, self.y, self.x + self.size, self.y + self.size], fill=self.color, outline="black")

class Circle(Shape):
    def draw(self, drawing):
        drawing.ellipse([self.x, self.y, self.x + self.size, self.y + self.size], fill=self.color, outline="black")

class Diamond(Shape):
    def draw(self, drawing):
        points = [
            (self.x + self.size // 2, self.y),
            (self.x + self.size, self.y + self.size // 2),
            (self.x + self.size // 2, self.y + self.size),
            (self.x, self.y + self.size // 2)
        ]
        drawing.polygon(points, fill=self.color, outline="black")

class Triangle(Shape):
    def draw(self, drawing):
        points = [
            (self.x + self.size // 2, self.y),
            (self.x, self.y + self.size),
            (self.x + self.size, self.y + self.size)
        ]
        drawing.polygon(points, fill=self.color, outline="black")

class Hexagon0(Shape):
    def draw(self, drawing):
        points = [(self.x + self.size * math.cos(math.radians(60 * i)),
                   self.y + self.size * math.sin(math.radians(60 * i)))
                   for i in range(6)]
        drawing.polygon(points, fill=self.color, outline="black")
class Hexagon45(Shape):
    def draw(self, drawing):
        points = []
        for i in range(6):
            angle = math.radians(60 * i + 45)
            x_point = self.x + self.size * math.cos(angle)
            y_point = self.y + self.size * math.sin(angle)
            points.append((x_point, y_point))
        drawing.polygon(points, fill=self.color, outline="black")
class Hexagon90(Shape):
    def draw(self, drawing):
        points = [(self.x + self.size * math.cos(math.radians(60 * i + 90)),
                   self.y + self.size * math.sin(math.radians(60 * i + 90)))
                   for i in range(6)]
        drawing.polygon(points, fill=self.color, outline="black")


palettes = [    ['darkslategray', 'darkseagreen', 'teal', 'yellowgreen', 'olivedrab'],
                ['darkslateblue', 'lightblue', 'navy', 'lightgray'],
                ['Forest Green', 'Golden Ochre', 'Deep Teal', 'Pearl White', 'Crimson Red'],
                ['darkolivegreen', 'khaki', 'steelblue', 'saddlebrown', 'darkseagreen'],
                ['Royal Purple', 'Cornflower Blue', 'Sky Blue', 'Steel Blue', 'Navy Blue'],
                ['brown', 'goldenrod', 'darkseagreen', 'darkcyan', 'lightgreen']
                ]
shapes = {
    "Square": Square,
    "Triangle": Triangle,
    "Circle": Circle,
    "Diamond": Diamond,
    "Hexagon0": Hexagon0,
    "Hexagon45": Hexagon45,
    "Hexagon90": Hexagon90
}

DATA_PATH = "static/data/patrimoine_marocain_ameliore.csv"
data = pd.read_csv(DATA_PATH, delimiter=';', skiprows=1, encoding='latin1')

def afficher_carte():
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': ccrs.PlateCarree()})

    ax.set_extent([-17, -1, 21, 36], ccrs.PlateCarree())  # Longitudes et latitudes approximatives du Maroc

    ax.add_feature(cfeature.BORDERS, linewidth=1.2)
    ax.coastlines()

    category_colors = {
        "Artisanat": "orange",
        "Architecture": "blue",
        "Culture": "yellow",
        "Musique": "red"
    }

    data["color"] = data["Type"].map(category_colors).fillna("gray")

    ax.scatter(
        data["Longitude"], data["Latitude"],
        color=data["color"], marker='o', s=100, transform=ccrs.PlateCarree()
    )

    for _, row in data.iterrows():
        x_offset = 0.2
        y_offset = 0.2

        # Ajustement des coordonnées selon la ville
        city_offsets = {
            "Fez": (-0.4, -0.4),
            "Meknes": (0.7, 0.2),
            "Casablanca": (0, -0.4),
            "Essaouira": (0.1, -0.3),
            "Chefchaouen": (0.2, 0),
            "Agadir": (0.2, -0.2),
            "Guelmim": (0.2, -0.2),
            "Dakhla": (0.2, -0.2)
        }

        x_offset, y_offset = city_offsets.get(row["Ville"], (0.2, 0.2))

        ax.text(
            row["Longitude"] + x_offset, row["Latitude"] + y_offset,
            row["Ville"], fontsize=12, color='darkblue',
            fontweight='bold', fontfamily='serif',
            transform=ccrs.PlateCarree()
        )

    handles = [
        plt.Line2D([0], [0], marker='o', color='w', label=cat, markersize=10,
                   markerfacecolor=color) for cat, color in category_colors.items()
    ]
    ax.legend(handles, category_colors.keys(), title="Types de Patrimoine", loc='lower right')

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plot_url = base64.b64encode(buf.getvalue()).decode('utf8')
    return plot_url

HEATMAP_DIR = "static/heatmaps"


def create_heatmap(type_patrimoine):
    filtered_df = data[data['Type'] == type_patrimoine]

    pivot_df = filtered_df.pivot_table(index='Patrimoine', columns='Ville', values='Latitude', aggfunc='count',
                                       fill_value=0)

    plt.figure(figsize=(5, 5))
    sns.heatmap(pivot_df, annot=True, cmap='viridis', linewidths=0.5)
    plt.title(f"Heatmap for Heritage Type: {type_patrimoine}")

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    heatmap_url = base64.b64encode(buf.getvalue()).decode('utf8')
    return heatmap_url
def generate_and_store_heatmaps():
    types = ["Artisanat", "Musique", "Architecture", "Culture"]

    for type_patrimoine in types:

        filtered_df = data[data['Type'] == type_patrimoine]

        pivot_df = filtered_df.pivot_table(index='Patrimoine', columns='Ville', values='Latitude', aggfunc='count',
                                           fill_value=0)

        plt.figure(figsize=(11, 8))
        sns.heatmap(pivot_df, annot=True, cmap='viridis', linewidths=0.5)
        plt.title(f"Heatmap for Heritage Type: {type_patrimoine}")
        heatmap_file_path = os.path.join(HEATMAP_DIR, f"{type_patrimoine.lower()}.png")
        plt.savefig(heatmap_file_path)
        plt.close()
app = Flask(__name__)


# 1. GALLERY
@app.route('/')
def index():
    return render_template("index.html")


@app.route('/gallery')
def gallery():
    images = os.listdir("static/gallery")
    return render_template("gallery.html", images=images)


# 2. GENERATE MOROCCAN TILE
@app.route('/generate')
def generate():
    return render_template("generate.html")

@app.route('/generate_tile', methods=['POST'])
def generate_new_tile():
    data = request.json
    selected_shape = data.get("shape")
    selected_size = int(data.get("size")) if data.get("size") else 100

    shape_type = shapes.get(selected_shape, random.choice(list(shapes.values())))

    img = generate_Tile(size=selected_size, shape_type=shape_type)
    img_path = f"static/generated/Tile_{random.randint(1000, 9999)}.png"
    img.save(img_path)

    return jsonify({"image": img_path})

def generate_Tile(size=100, num_rows=12, num_cols=12, shape_type=Square):
    img = Image.new('RGB', (500, 500), (255, 255, 255))
    drawing = ImageDraw.Draw(img)

    selected_palette = random.choice(palettes)

    for row in range(num_rows):
        for col in range(num_cols):
            x, y = col * size, row * size
            color = random.choice(selected_palette)

            if shape_type in [Hexagon0, Hexagon45, Hexagon90]:
                new_size = size * 0.6
                if shape_type == Hexagon0:
                    x, y = 2 * col * new_size, 1.7 * row * new_size
                elif shape_type == Hexagon45:
                    x, y = 1.8 * col * new_size, 1.8 * row * new_size
                elif shape_type == Hexagon90:
                    x, y = 1.7 * col * new_size, 2 * row * new_size
            else:
                new_size = size

            shape = shape_type(x, y, color, new_size)
            shape.draw(drawing)

    return img


# 3. IMAGE FILTERING
@app.route('/imagefilter')
def imagefilter_page():
    return render_template("imagefilter.html")

@app.route('/imagefilter/apply', methods=['POST'])
def apply_image_filter():
    file = request.files['image']
    image = Image.open(file).convert("L")

    image_path = f"static/generated/filtered_image_{random.randint(1000, 9999)}.png"
    image.save(image_path)

    return jsonify({"image": image_path})


# 5. AUDIO FILTERING
@app.route("/audiofilter")
def audiofilter_page():
    return render_template("audiofilter.html")

@app.route('/audiofilter/apply', methods=['POST'])
def apply_audio_filter():
    file1 = request.files.get('audio1')
    file2 = request.files.get('audio2')

    filename1 = secure_filename(file1.filename)
    temp_audio_path1 = os.path.join('static/uploads', filename1)
    file1.save(temp_audio_path1)

    filename2 = secure_filename(file2.filename)
    temp_audio_path2 = os.path.join('static/uploads', filename2)
    file2.save(temp_audio_path2)

    audio1 = AudioSegment.from_file(temp_audio_path1)
    audio2 = AudioSegment.from_file(temp_audio_path2)

    mixed = audio1.overlay(audio2)

    mixed_audio_filename = f"filtered_audio_{random.randint(1000, 9999)}.wav"
    mixed_audio_path = os.path.join('static/generated', mixed_audio_filename)
    mixed.export(mixed_audio_path, format="wav")

    os.remove(temp_audio_path1)
    os.remove(temp_audio_path2)

    mixed_audio_url = f"/{mixed_audio_path}"
    return jsonify({"mixed_audio_url": mixed_audio_url})


# 4. DOWNLOAD IMAGE
@app.route('/download/<filename>')
def download_image(filename):
    file_path = os.path.join("static/uploads", filename)
    return send_file(file_path, as_attachment=True)


@app.route('/visualisation')

def visualisation():
    return render_template('visualisation.html', plot_url=afficher_carte(), heatmap_url=None)

@app.route('/heatmap/<type_patrimoine>')
def heatmap(type_patrimoine):
    heatmap_url = f"/static/heatmaps/{type_patrimoine.lower()}.png"
    return render_template('visualisation.html', plot_url=afficher_carte(), heatmap_url=heatmap_url)


if __name__ == '__main__':
    generate_and_store_heatmaps()
    app.run(debug=True)
