import converters.structural
import converters.office
from gui.app import FormatFlowApp


def main():
    print("Initializing application...")

    app = FormatFlowApp()
    app.mainloop()

    print("Application closed.")


if __name__ == "__main__":
    main()
