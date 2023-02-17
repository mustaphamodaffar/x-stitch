from img2xstitch.utils import PreprocessImg, MapImgToThread, MapImgToPattern
import pathlib
import argparse


def run(img_raw_path, cnt_stitch, cnt_colors, max_dim_abs_size):
    preprocess_instance = PreprocessImg(img_raw_path=img_raw_path,
                                        max_dim_abs_size=max_dim_abs_size)
    scaled_image = preprocess_instance.run()
    map_thread_instance = MapImgToThread(thread_map_path='static/dmc_dict.csv',
                                         img_input=scaled_image,
                                         cnt_stitch=cnt_stitch,
                                         cnt_colors=cnt_colors)
    color_mapped_image, df_colors = map_thread_instance.run()
    map_pattern_instance = MapImgToPattern(img_input=color_mapped_image,
                                           cnt_colors=cnt_colors)
    img_output = map_pattern_instance.run(df_colors=df_colors)

    img_filename = pathlib.PurePath(img_raw_path).name
    output_directory = 'test_outputs/'
    pathlib.Path(output_directory).mkdir(parents=True, exist_ok=True)
    img_output.save(output_directory + img_filename)

    img_output.show()


if __name__ == '__main__':
    parse = argparse.ArgumentParser()
    parse.add_argument("--path",
                       required=True,
                       help="The relative path to your image. So far pipeline has been tested on .jpg formats")
    parse.add_argument("--stitchcount",
                       type=int,
                       default=10,
                       help="The aida stitch count. Not incorporated into the script yet.")
    parse.add_argument("--colors",
                       type=int,
                       default=15,
                       help="The number of different thread colors the pattern should have.")
    parse.add_argument("--maxsize",
                       type=int,
                       default=100,
                       help="The desired length or width, whichever is larger - depends on orientation of input image.")
    input_args = parse.parse_args()

    run(input_args.path, input_args.stitchcount, input_args.colors, input_args.maxsize)
