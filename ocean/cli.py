"""CLI entry point — delegates to ``ocean.cli``.

Usage:

    python -m ocean.cli            # → invokes ``ocean`` CLI group

Or install the ``ocean`` console_scripts entry point:

    ocean train ...                 # training
    ocean cloud upload ...          # AI Studio upload
"""

from ocean.cli import main

if __name__ == "__main__":
    main()
