from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys


commands = [
    "/q",
    "/quit",
    "/clear",
    "/history",
    "/help",
]

command_completer = WordCompleter(
    commands,
    ignore_case=True,
    sentence=True
)

kb = KeyBindings()

@kb.add("enter")
def _(event):
    buffer = event.app.current_buffer
    text = buffer.text

    # If line ends with "\" → insert newline
    if text.endswith("\\"):
        buffer.delete_before_cursor(1)  # remove the "\"
        buffer.insert_text("\n")
    else:
        # otherwise submit
        buffer.validate_and_handle()

# SESSION
session = PromptSession(
    completer=command_completer,
    multiline=True,
    key_bindings=kb
)


def get_user_input():
    return session.prompt(
        HTML("<b><ansicyan>You:</ansicyan></b> "),
        bottom_toolbar=HTML("<ansigray>Enter = send | \\ + Enter = new line</ansigray>")
    ).strip()