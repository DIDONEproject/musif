import argparse
import os
import sys
from os import path
from typing import List

from pandas import DataFrame

from musif import VERSION
from musif.features.extract import FeaturesExtractor


def choose_parts(xml_dir: str) -> List[str]:
    """
    Function to let the user choose the instrument to work with given all the instruments in his/her corpus #
    """
    # score_infos = ScoreInfoExtractor(sequential=sequential).from_dir(xml_dir)
    # unique_abbreviated_parts = list(set(list(itertools.chain(*[score_info.real_scoring.split(',') for score_info in score_infos]))))
    # if '' in unique_abbreviated_parts:
    #     unique_abbreviated_parts.remove('')
    # parts = []
    # for abbreviated_part in unique_abbreviated_parts:
    #     abbreviated_instrument, part_number = extract_instrument_and_number_from_part(abbreviated_part)
    #     part = to_part_name(abbreviation_to_sound[abbreviated_instrument], part_number)
    #     parts.append((abbreviated_part, part))
    # parts.sort()
    # options = {str(i): f"{str(i)} - {part[1]}" for i, part in enumerate(parts, 1)}
    # print('Which part do you want to process?:')
    # print('\n'.join(list(options.values())))
    # choice = input('Please, type the number(s) associated to the part separated by comma or space: ').strip()
    # sequence = choice.split(',')
    # if len(sequence) < 2:
    #     sequence = choice.split(' ')
    # chosen_parts = ','.join([parts[int(number.strip())-1][0] for number in sequence])
    # return chosen_parts
    return ["obI", "obII"]

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
    chosen_parts = choose_parts(args.xml)
    features = FeaturesExtractor().from_dir(args.xml, chosen_parts)
    print(features)
    write_files(args, features)


if __name__ == "__main__":
    main()
