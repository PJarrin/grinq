from importlib.resources import files

def file_name(file):
    return str(files(__package__) / file)