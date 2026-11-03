from dataclasses import dataclass

from tqdm import tqdm


@dataclass()
class ProgressBar:
    max_num: int
    bar_colour: str = "WHITE"
    is_descbar_persist: bool = False
    __progress_bar: tqdm = None
    __progress_desc: tqdm = None

    def __post_init__(self):
        self.__progress_bar = tqdm(
            initial=0,
            total=self.max_num,
            colour=self.bar_colour,
            bar_format="{bar} {n_fmt}/{total_fmt} ({percentage:3.0f}%) [{elapsed}] ",
        )
        self.__progress_desc = tqdm(
            position=1, bar_format="{desc}", desc="", leave=False
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.is_descbar_persist:
            self.__progress_desc.set_description("")
            self.__progress_desc.refresh()
        self.__progress_bar.close()
        self.__progress_desc.close()

    def update_bar(self, n=1):
        self.__progress_bar.update(n)
        self.__progress_bar.refresh()

    def update_desc(self, text: str):
        self.__progress_desc.set_description(text)
        self.__progress_desc.refresh()
