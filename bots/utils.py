# Python implementation to
# read last N lines of a file

# Function to read
# last N lines of the file
def read_last_n_lines(file_name, N):
    with open(file_name) as file:
        return file.readlines()[-N:]
