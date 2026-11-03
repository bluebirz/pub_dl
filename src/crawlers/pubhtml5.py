import re
from collections import namedtuple
from pathlib import Path

import img2pdf
from bs4 import BeautifulSoup
from pypdf import PdfWriter

from components.file_manager import (
    get_filesize,
    list_images,
    make_folder,
    move_file,
    remove_folder,
)
from components.log_manager import CustomLog
from components.progress_bar import ProgressBar
from components.utils import gen_id
from components.web_scraper import WebScraper

PREFIX = "pubhtml5"
REGEX = r".*pubhtml5\.com"
METADATA = namedtuple("metadata", ["title", "pages"])
MAX_FILESIZE_BEFORE_COMPRESSION_MB = 100
COMPRESSION_LEVEL = 10


def __get_img_url(frame, page_id: int):
    def __go_next(frame):
        frame.locator("div.flipbutton.downbutton.right").click()
        frame.wait_for_timeout(1_000)

    is_seeking = True
    while is_seeking:
        if not (
            target_page := BeautifulSoup(frame.content(), "html.parser").find(
                "div", {"id": f"page{page_id}"}
            )
        ):
            __go_next(frame)
            continue
        if not (target_img := target_page.find("img")):
            __go_next(frame)
            continue
        is_seeking = False
    img_src = target_img["src"]
    return frame.url + img_src


def __process_scrape_image(
    ws: WebScraper, total_pages: int, target_folder: str, logger: CustomLog
) -> bool:
    url_trunk = re.compile(r"https?:\/\/(\w+\.)?(\w+\.\w+\/\w+\/\w+)\/.*").split(
        ws.page.url
    )
    iframe_url = f"https://online.{''.join([t for t in url_trunk if t])}/"
    frame = ws.page.frame(url=iframe_url)
    is_done = True
    message_queue = []
    with ProgressBar(max_num=total_pages) as pb:
        for i in range(1, total_pages + 1):
            url = __get_img_url(frame, i)
            # print(f"{i=}: {url=}")
            path = f"{i}.{url.split(".")[-1]}"
            dl_passed, msg = ws.download(
                img_url=url,
                img_download_path=(Path(target_folder) / Path(path)).as_posix(),
            )
            if not dl_passed:
                message_queue.append(msg)
            is_done = is_done and dl_passed
            pb.update_bar()
            pb.update_desc(msg)
    if len(message_queue) > 0:
        logger.error(f"Found failed downloads by {len(message_queue)} items")
        for m in message_queue:
            logger.error(m)
    return is_done


def __get_metadata(bs: BeautifulSoup) -> METADATA:
    title_tag = (
        (
            e[0].get_text(strip=True)
            if (e := bs.find_all("title")) and len(e) > 0
            else None
        )
        .split("|")[0]
        .split("-")
    )
    metadata = METADATA(title=title_tag[0].strip(), pages=int(title_tag[-1]))
    return metadata


def __build_pdf(source_folder: str, target_pdf_path: str) -> None:
    dl_list = list_images(source_folder, is_order_by_time=True)
    with open(target_pdf_path, "wb") as f:
        f.write(img2pdf.convert(dl_list))


def __compress_pdf(old_path: str, new_path: str, level: int = 50) -> None:
    writer = PdfWriter(clone_from=old_path)

    cnt_pages = len(writer.pages)
    with ProgressBar(max_num=cnt_pages) as pbar:
        for page in writer.pages:
            for img in page.images:
                img.replace(img.image, quality=level)
            pbar.update_bar()
        writer.write(new_path)

    return True


def export_pdf(url: str, parent_folder: str) -> None:
    tmp_id = gen_id(PREFIX)
    tmp_folder = (Path(parent_folder) / Path(PREFIX) / Path(tmp_id)).as_posix()

    # download images
    logger = CustomLog(logger_name=tmp_id)
    logger.info(url)
    with WebScraper(url, is_headless=False, user_data_dir=PREFIX) as ws:
        ws.check_cloudflare_turnstile()
        base_html = ws.get_html()
        title, pages = __get_metadata(base_html)
        logger.info(f"Title: {title}")
        logger.info(f"Total pages: {pages}")
        make_folder(tmp_folder)
        # pages = 5
        is_done = __process_scrape_image(
            ws=ws, total_pages=pages, target_folder=tmp_folder, logger=logger
        )
        logger.info(f"download status: {'success' if is_done else 'failed'}")

    # download failed --> cleanup and abort
    if not is_done:
        logger.error("download failed. aborting...")
        remove_folder(tmp_folder)
        return

    # create pdf
    tmp_pdf_path = (Path(tmp_folder) / Path(f"{title}.pdf")).as_posix()
    real_pdf_path = (
        Path(parent_folder) / Path(PREFIX) / Path(f"{title}.pdf")
    ).as_posix()
    logger.info(f"creating pdf: {tmp_pdf_path}")
    __build_pdf(source_folder=tmp_folder, target_pdf_path=tmp_pdf_path)

    # compress pdf
    if (
        pdf_size := get_filesize(tmp_pdf_path) / (1024 * 1024)
    ) > MAX_FILESIZE_BEFORE_COMPRESSION_MB:
        logger.info(
            f"file size ({pdf_size:.2f} Mb) is bigger than {MAX_FILESIZE_BEFORE_COMPRESSION_MB} Mb. performing compression..."
        )
        __compress_pdf(
            old_path=tmp_pdf_path, new_path=real_pdf_path, level=COMPRESSION_LEVEL
        )
    else:
        logger.info("file is small enough. moving to parent folder.")
        move_file(src=tmp_pdf_path, dst=real_pdf_path)

    # cleanup and report
    logger.info(
        f"final pdf is at {real_pdf_path} ({get_filesize(real_pdf_path) / (1024 * 1024):.2f} Mb)"
    )
    logger.info(f"removing temp folder: {tmp_folder}")
    remove_folder(tmp_folder)
    logger.info("completed")
