import random
import string
from string import digits, ascii_uppercase


# This function is for generating a random combines int and string for file links
legals = digits + ascii_uppercase
def rand_link(length, char_set=legals):

    link = ''
    for _ in range(length): link += random.choice(char_set)
    return link

def generate_file_link(file_name):

    link = rand_link(120)
    # Add random string to filename
    ext = file_name.rsplit('.', 1)[1]
    link = link + '.' + ext
    return link
