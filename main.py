import cv2
import os
import penplotter.img2sketch as img2sketch
import sys
import argparse
import penplotter.interface as interface
import penplotter.imageUtils as imageUtils

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate Arduino contours from an image.')
    parser.add_argument('input', help='Input image file path')
    parser.add_argument('output', help='Output file path')
    parser.add_argument('--n', type=int, default=0, help='n parameter (default: 0)')
    parser.add_argument('--canny_threshold1', type=int, default=125, 
                       help='First threshold for Canny edge detector (default: 125)')
    parser.add_argument('--canny_threshold2', type=int, default=130,
                       help='Second threshold for Canny edge detector (default: 130)')
    parser.add_argument('--pen_diameter', type=float, default=1.5,
                       help='Pen diameter for drawing (default: 1.5)')
    parser.add_argument('--max_width', type=int, default=2200,
                       help='Maximum width parameter (default: 2200)')
    parser.add_argument('--multiplier', type=int, default=6,
                       help='Multiplier factor (default: 6)')
    parser.add_argument('--scale', type=float, default=0.4,
                       help='Scale factor for the output (default: 0.4)')
    args = parser.parse_args()

    frame = cv2.imread(args.input)
    i2s = img2sketch.PencilSketch()
    
    sketch_result = i2s(frame)
    if sketch_result is None:
        print("ta finahiya had tswira??")
        sys.exit()

    processed_image = sketch_result
    
    try:
        os.mkdir(args.output)
    except FileExistsError:
        print(f"Directory '{args.output}' already exists.")
    except Exception as e:
        print(f"hhh wtf: {e}")
        sys.exit(1)
    
        img=processed_image,

    contours = imageUtils.image_to_contours(
        img=sketch_result,
        n=args.n,
        canny_threshold1=args.canny_threshold1,
        canny_threshold2=args.canny_threshold2,
        pen_diameter=args.pen_diameter,
        max_width=args.max_width,
        multiplier=args.multiplier
    )
    
    interface.show_and_save(contours=contours, scale=args.scale, offset_x=0, offset_y=0, container=args.max_width, output_file=args.output)