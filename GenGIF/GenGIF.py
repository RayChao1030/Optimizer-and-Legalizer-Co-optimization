import argparse
from layout_parser import parse_files
from layout_visualizer import visualize_steps, generate_animation

def main():
    parser = argparse.ArgumentParser(description="Generate GIF/MP4 for layout optimization steps.")
    parser.add_argument("-lg", required=True, help="Input .lg file.")
    parser.add_argument("-opt", required=True, help="Input .opt file.")
    parser.add_argument("-postlg", required=True, help="Input .postlg file.")
    parser.add_argument("-o", required=True, help="Output GIF/MP4 file.")
    args = parser.parse_args()

    # Parse files
    layout_data, opt_steps, post_layout = parse_files(args.lg, args.opt, args.postlg)

    # Generate visualization frames
    frames = visualize_steps(layout_data, opt_steps, post_layout)

    # Save as GIF or MP4
    generate_animation(frames, args.o)

if __name__ == "__main__":
    main()
