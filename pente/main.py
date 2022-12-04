import os
import sys

usage = f"""usage: {sys.argv[0]} [ui]
  ui: one of cli or gui
      (default: cli)
"""

sys.path.append(os.getcwd())
if len(sys.argv) < 2 or sys.argv[1] == "cli":
    from pente.cli.Cli import Cli
    Cli().mainloop()
elif sys.argv[1] == "gui":
    from pente.gui.Gui import Gui
    Gui().mainloop()
else:
    print(usage)
