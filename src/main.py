import re

import click

from components.file_manager import is_exists, is_file, read_yaml
from components.log_manager import CustomLog
from components.utils import gen_id
from crawlers import pubhtml5

logger = CustomLog(logger_name=gen_id(__name__))


def process_input(url_list: list):
    url_cnt = len(url_list)
    main_output_folder = "output"
    for idx, url in enumerate(url_list):
        logger.info(f"#{idx+1}/{url_cnt} > {url}")
        if re.compile(pubhtml5.REGEX).match(url):
            pubhtml5.export_pdf(url, main_output_folder)
        else:
            logger.error(f"{url} does not match with any crawlers")


@click.command()
@click.argument("input", help="An url or YAML file containing a list of urls")
def main(input: str):
    logger.info(f"{input=}")

    if is_file(input):
        if not is_exists(input):
            raise FileNotFoundError(f"{input} is a file yet not found.")
        input_list = read_yaml(input)
        process_input(input_list)
    elif input.startswith("http"):
        process_input([input])
    else:
        raise ValueError(f"{input} is neither a file nor a url.")


if __name__ == "__main__":
    main()
