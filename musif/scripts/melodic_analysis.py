import argparse
import re
import sys
from os import path
from typing import List

from musif.extract.extract import FeaturesExtractor, PartsExtractor
from pandas import DataFrame

from musif import VERSION


def choose_parts(xml_dir: str, config_file: str) -> List[str]:

    parts = PartsExtractor(config_file).extract(xml_dir)
    options = {str(i): f"{i} - {part}" for i, part in enumerate(parts, 1)}
    print('Which part do you want to process?:')
    print('\n'.join(list(options.values())))
    choice = input('Please, type the number(s) associated to the part separated by commas or spaces, or just press Enter to select all: ').strip()
    if choice == '':
        return []
    sequence = re.findall(r"[\d']+", choice)
    if len(sequence) < 2:
        sequence = choice.split(' ')
    chosen_parts = [parts[int(number.strip())-1] for number in sequence]
    return chosen_parts


def write_files(args: argparse.Namespace, features: DataFrame):
    pass
#     if not any(df.shape[0] != 0 for df in all_dataframes):
#         print("There has been a problem in the information extraction process from the scores. Please, execute the program again.")
#         print("If the problem persists open a issue on GitHub and it will be solved as soon as possible.")
#         return
#     if not path.exists(args.output_dir):
#         mkdir(args.output_dir)
#     results_folder = path.join(args.output_dir, instrument_complete)
#     if not path.exists(results_folder):
#         mkdir(results_folder)
#     start_time = datetime.now()
#     write.write(all_dataframes, results_folder, args.factors, args.sequential)
#     print(f'The information generation process lasted {(datetime.now() - start_time).seconds//60} minutes')


def parse_args(args_list: list) -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "xml",
        help="XML directory containing input files.",
    )
    parser.add_argument(
        "-c", "--config",
        default="config.yml",
        help="Config file.",
    )
    parser.add_argument(
        "-f", "--factors",
        type=int,
        choices=[0, 1, 2],
        default=0,
        help="Number of factors.",
    )
    parser.add_argument(
        "-v", "--version", action="version", version=f"musif {VERSION}"
    )

    args = parser.parse_args(args_list)

    if args.xml is None:
        print(f"An XML directory must be passed.")
        sys.exit(2)

    if not path.exists(args.xml):
        print(f"XML directory {args.xml} doesn't exist")
        sys.exit(2)

    return args


def main():

    args = parse_args(sys.argv[1:])
    chosen_parts = choose_parts(args.xml, args.config)
    features = FeaturesExtractor(args.config).from_dir(args.xml, chosen_parts)
    write_files(args, features)


if __name__ == "__main__":
    main()
