import os
import hydra

import tkinter as tk
import customtkinter as ctk
from omegaconf import DictConfig

@hydra.main(version_base=None, config_path='.', config_name='config')
def main(config: DictConfig) -> None:
    ctk.set_appearance_mode('dark')
    root = ctk.CTk()
    root.geometry('600x600')
    scroll_bar = ctk.CTkScrollbar(master=root, orientation='horizontal')
    scroll_bar.place(relx=0.5, rely=0.8, anchor='center')

    root.mainloop()


if __name__ == '__main__':
    main()

