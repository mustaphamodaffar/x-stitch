import logging
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from sklearn.cluster import KMeans
from scipy.spatial import distance, cKDTree
import random

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO, datefmt='%d-%b-%y %H:%M:%S')


class PreprocessImg:
    """Contort the input image to our specifications"""

    def __init__(self, img_raw_path: object, max_dim_abs_size: object) -> object:
        self.img_raw_path = img_raw_path
        self.img_raw_width = None
        self.img_raw_height = None
        self.img_raw_format = None
        self.img_raw_orientation = None

        self.max_dim_abs_size = max_dim_abs_size
        self.img_scaled_width = None
        self.img_scaled_height = None

    def get_img_attr(self):
        """Get width, height and image format"""
        with Image.open(self.img_raw_path) as img_raw:
            self.img_raw_width, self.img_raw_height = img_raw.size
            self.img_raw_format = img_raw.format

    def get_orientation(self):
        """Get the image orientation based on a comparison of height and width"""
        if self.img_raw_height >= self.img_raw_width:
            self.img_raw_orientation = 'Portrait'
        else:
            self.img_raw_orientation = 'Landscape'

    def calc_scaled_size(self):
        """Calculate scaled size based on maximum absolute size provided while maintaining aspect ratio"""
        img_scale_factor = self.max_dim_abs_size / max(self.img_raw_height, self.img_raw_width)

        if self.img_raw_orientation == 'Portrait':
            self.img_scaled_height = self.max_dim_abs_size
            self.img_scaled_width = int(self.img_raw_width * img_scale_factor)
        elif self.img_raw_orientation == 'Landscape':
            self.img_scaled_width = self.max_dim_abs_size
            self.img_scaled_height = int(self.img_raw_height * img_scale_factor)

    def get_scaled_image(self):
        """Scale the image using dimensions provided"""
        tuple_size = (self.img_scaled_width, self.img_scaled_height)
        with Image.open(self.img_raw_path) as img_raw:
            img_scaled = img_raw.resize(size=tuple_size, resample=Image.LANCZOS)  # Slowest but highest quality filter

        return img_scaled

    def run(self):
        """Take an input image and get attributes required to scale an input image"""
        self.get_img_attr()
        self.get_orientation()
        self.calc_scaled_size()
        img_scaled = self.get_scaled_image()

        return img_scaled


class MapImgToThread:
    """Map pixels to closest thread colours"""

    def __init__(self, thread_map_path, img_input, cnt_stitch, cnt_colors):
        self.thread_map_path = thread_map_path
        self.img_input = img_input
        self.cnt_stitch = cnt_stitch
        self.cnt_colors = cnt_colors

        self.thread_palette = None

    def create_thread_palette(self):
        """Load the RGB to floss mapping and return RGB tuples as a list"""
        self.df_thread_map = pd.read_csv(self.thread_map_path)
        self.df_thread_map['rgb_tuple'] = list(zip(self.df_thread_map.r, self.df_thread_map.g, self.df_thread_map.b))

        self.thread_palette = self.df_thread_map['rgb_tuple'].tolist()

    def map_img_colors(self):
        """Convert the input image to use the colours constrained by the thread palette provided"""

        # Perform color quantization by use of the k-means method
        arr_input_img = np.array(self.img_input)
        arr_reshape_img = arr_input_img.reshape(-1, 3)

        kmeans = KMeans(n_clusters=self.cnt_colors, random_state=7).fit(arr_reshape_img)
        color_labels = kmeans.labels_
        color_centers = kmeans.cluster_centers_
        arr_quantized_img = color_centers[color_labels].reshape(arr_input_img.shape).astype('uint8')

        # Map the unique quantized colors to our thread palette using a nearest neighbors approach
        thread_palette_tree = cKDTree(self.thread_palette)
        # Limit our query to the single best color match
        thread_distances, thread_indices = thread_palette_tree.query(arr_quantized_img.reshape(-1, 3), k=1)
        # Create the output array
        arr_thread_palette = np.array(self.thread_palette)
        arr_output_img = arr_thread_palette[thread_indices].reshape(arr_input_img.shape).astype('uint8')
        output_img = Image.fromarray(arr_output_img)

        # Create an output df of the thread colors in the output image
        df_output_palette = self.df_thread_map[self.df_thread_map.index.isin(set(thread_indices))]

        # Create a summary of the thread colors, add into logging later
        for i, v in enumerate(set(thread_indices)):
            print("Closest DMC RGB color: ", self.df_thread_map['rgb_tuple'].iloc[v])
            print("Closest DMC floss code: ", self.df_thread_map['floss'].iloc[v])
            print("Closest DMC floss name: ", self.df_thread_map['description'].iloc[v], "\n")

        return output_img, df_output_palette

    def run(self):
        """Take the inputs and return an image mapped to the specified thread palette"""
        self.create_thread_palette()
        output_img, df_output_palette = self.map_img_colors()

        return output_img, df_output_palette


class MapImgToPattern:
    """Apply the overlays required to return a cross stitch pattern over the input image with a thread key"""

    def __init__(self, img_input, cnt_colors, enlarge_factor=25):
        self.img_input = img_input
        self.enlarge_factor = enlarge_factor
        self.cnt_colors = cnt_colors

    def img_enlarge(self):
        enlarged_img_size = (self.img_input.width*self.enlarge_factor, self.img_input.height*self.enlarge_factor)
        img_enlarged = self.img_input.resize(size=enlarged_img_size, resample=Image.NEAREST)
        return img_enlarged

    def add_gridlines(self, img_enlarged, color, step_size):
        """ Add a border to distinguish each pixel or a group of pixels"""
        draw = ImageDraw.Draw(img_enlarged)

        y_start = 0
        y_end = img_enlarged.height

        for x in range(0, img_enlarged.width, step_size):
            line = ((x, y_start), (x, y_end))
            draw.line(line, fill=color)

        x_start = 0
        x_end = img_enlarged.width

        for y in range(0, img_enlarged.height, step_size):
            line = ((x_start, y), (x_end, y))
            draw.line(line, fill=color)

        del draw
        return img_enlarged

    def map_colors_to_symbols(self, df_colors):
        """Create a list of symbols that can used to represent each color on the pattern"""
        symbols = []
        # The geometric shapes segment of the unicode character kingdom contains 96 symbols
        # So our color limit is 96 colors, unless we want to repeat symbols...
        for i in range(0x25A0, 0x2600):
            symbol = chr(i)
            symbols.append(symbol)

        # Get the symbol quantity required and assign to our palette
        random_symbols = random.sample(symbols, len(df_colors))
        df_colors['symbol'] = random_symbols

        return df_colors

    def add_symbols(self, df_colors, img_input, step_size):
        """Superimpose the mapped symbols onto each stitch in the pattern"""
        # Most default fonts wouldn't work
        symbol_font = ImageFont.truetype('static/BabelStoneHan.ttf', 20)
        draw = ImageDraw.Draw(img_input)

        # This will be slow and needs to be looked at when it comes to the efficiency stage
        for x in range(0, img_input.width, step_size):
            for y in range(0, img_input.height, step_size):
                pixel = img_input.getpixel((x, y))
                df_pixel = df_colors[df_colors['rgb_tuple'] == pixel]
                draw.text((x, y), df_pixel['symbol'].values[0], font=symbol_font, fill='black')

        del draw
        return img_input

    def run(self, df_colors):
        step_size = self.enlarge_factor
        enlarged_image = self.img_enlarge()
        df_colors_symbols = self.map_colors_to_symbols(df_colors)
        img_symbols = self.add_symbols(df_colors_symbols, enlarged_image, step_size)

        minor_gridlines_image = self.add_gridlines(img_symbols, 'grey', step_size)
        major_gridlines_image = self.add_gridlines(minor_gridlines_image, 'black', step_size*10)

        return major_gridlines_image

