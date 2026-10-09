"""Uygulamanın başlangıç noktası:  python main.py"""

from frontend.main_window import AnaPencere


def main() -> None:
    pencere = AnaPencere()
    pencere.mainloop()


if __name__ == "__main__":
    main()
