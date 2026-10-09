try:
    from .cli.main import main
except ImportError:  # pragma: no cover
    from cli.main import main


if __name__ == "__main__":
    main()
